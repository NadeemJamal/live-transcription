"""
Flask Web Application for WAV File Testing
Provides browser-based interface for uploading and testing WAV files
"""

import os
import sys
import asyncio
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dataclasses import asdict

# Add parent directory to path to import testing framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from testing_framework.core.test_bot import (
    TestDataCollectorProcessor,
    AudioInjectorProcessor,
    TestReport,
    TurnResult
)
from testing_framework.core.menu_validator import MenuValidator
from testing_framework.core.error_detector import ErrorDetector
from testing_framework.core.order_analyzer import OrderAnalyzer
from saeed_balti.bot.saeed_balti_menu import MENU

from pipecat.frames.frames import StartFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.services.deepgram.flux.stt import DeepgramFluxSTTService

from dotenv import load_dotenv
from datetime import datetime
from loguru import logger
import json
import glob

load_dotenv(override=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['RESULTS_FOLDER'] = os.path.join(os.path.dirname(__file__), 'test_results')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)


async def process_wav_file(filepath: str, engines: list = None, use_keyterms: bool = True) -> TestReport:
    """
    Process a WAV file and return test report with error analysis

    Args:
        filepath: Path to WAV file
        engines: List of STT engines to use (default: ['deepgram'])
        use_keyterms: Enable menu vocabulary boosting (default: True)

    Returns:
        TestReport object with analysis results
    """
    from testing_framework.core.batch_stt_processor import process_audio_batch

    if engines is None:
        engines = ['deepgram']  # Default to Deepgram only

    logger.info(f"Processing with engines: {engines}")
    logger.info(f"Menu keyterm boosting: {'ENABLED' if use_keyterms else 'DISABLED'}")

    # Process with batch STT (fast!)
    engine_results = await process_audio_batch(filepath, engines, use_menu_keyterms=use_keyterms)

    # Use primary engine's results (prefer Deepgram Nova-2, then Nova-3, then Speechmatics, then first available)
    if 'deepgram-nova-2' in engine_results:
        primary_engine = 'deepgram-nova-2'
    elif 'deepgram-nova-3' in engine_results:
        primary_engine = 'deepgram-nova-3'
    elif 'speechmatics' in engine_results:
        primary_engine = 'speechmatics'
    else:
        primary_engine = list(engine_results.keys())[0]
    result = engine_results[primary_engine]

    logger.info(f"Using {primary_engine} as primary transcript")
    logger.info(f"Transcription completed in {result.duration_seconds:.2f}s")
    logger.info(f"Found {len(result.utterances)} utterances from {len(set(u.speaker for u in result.utterances))} speaker(s)")

    utterances = result.utterances

    # Store all engine results for comparison
    engine_data = {}
    for engine_name, eng_result in engine_results.items():
        engine_data[engine_name] = {
            'full_text': eng_result.full_text,
            'utterances': [asdict(u) for u in eng_result.utterances],
            'duration': eng_result.duration_seconds,
            'metadata': eng_result.metadata
        }

    logger.info(f"Stored results from {len(engine_data)} engine(s): {list(engine_data.keys())}")

    # Generate report
    report = TestReport(
        conversation_name=Path(filepath).stem,
        timestamp=datetime.now().isoformat()
    )

    turn = TurnResult(
        turn_number=1,
        wav_file=filepath,
        utterances=utterances,
        transcription=" ".join([u.text for u in utterances]),
        bot_response="",
        start_time=datetime.now()
    )
    report.add_turn(turn)

    # Run error detection and order analysis
    menu_validator = MenuValidator(MENU)
    error_detector = ErrorDetector(menu_validator)
    order_analyzer = OrderAnalyzer(menu_validator)

    # Detect errors in each utterance
    for turn_result in report.turns:
        for utterance in turn_result.utterances:
            errors = error_detector.detect_errors(utterance)
            utterance.errors.extend(errors)

            for error in errors:
                report.add_error(error.error_type)

    # Extract and validate order
    all_utterances = []
    for turn in report.turns:
        all_utterances.extend(turn.utterances)

    if all_utterances:
        order_summary = order_analyzer.extract_order(all_utterances)
        order_validation = order_analyzer.validate_order(order_summary)

        report.order_summary = order_summary
        report.order_validation = order_validation

    # Store multi-engine results for comparison
    report.engine_results = engine_data

    return report


@app.route('/')
def index():
    """Upload page with history"""
    # Get recent test results
    result_files = glob.glob(os.path.join(app.config['RESULTS_FOLDER'], '*.json'))
    result_files.sort(key=os.path.getmtime, reverse=True)  # Most recent first

    history = []
    for filepath in result_files[:10]:  # Show last 10
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                history.append({
                    'id': os.path.basename(filepath),
                    'name': data.get('conversation_name', 'Unknown'),
                    'timestamp': data.get('timestamp', ''),
                    'total_errors': data.get('total_errors', 0),
                    'order_status': 'PASSED' if data.get('order_validation', {}).get('is_correct') else 'FAILED'
                })
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            continue

    return render_template('index.html', history=history)


@app.route('/upload', methods=['POST'])
def upload_wav():
    """Handle WAV upload and process immediately"""
    try:
        if 'wav_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['wav_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.wav'):
            return jsonify({'error': 'Only WAV files allowed'}), 400

        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"Saving file to: {filepath}")
        file.save(filepath)
        print(f"File saved successfully, size: {os.path.getsize(filepath)} bytes")

        # Get engine selection (default: deepgram only)
        engines_param = request.form.get('engines', 'deepgram')
        engines = [e.strip() for e in engines_param.split(',')]

        # Map 'deepgram' to 'deepgram-nova-2' for backward compatibility
        engines = ['deepgram-nova-2' if e == 'deepgram' else e for e in engines]

        print(f"Using STT engines: {engines}")

        # Get keyterm setting from form (default: enabled)
        use_keyterms = request.form.get('use_keyterms', 'true').lower() == 'true'
        print(f"Menu keyterm boosting: {use_keyterms}")

        # Run test immediately (sync wrapper for async function)
        # Create new event loop for this thread (Flask uses worker threads)
        print("Creating event loop...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            print("Running batch STT...")
            test_report = loop.run_until_complete(
                process_wav_file(filepath, engines=engines, use_keyterms=use_keyterms)
            )
            print("Processing completed successfully")
        finally:
            loop.close()

        # Convert to dict for JSON response
        report_dict = asdict(test_report)

        # Convert order_summary and order_validation to dicts if they exist
        if test_report.order_summary:
            report_dict['order_summary'] = asdict(test_report.order_summary)
        if test_report.order_validation:
            report_dict['order_validation'] = asdict(test_report.order_validation)

        # Convert datetime objects to strings (recursively)
        def convert_datetimes(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetimes(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetimes(item) for item in obj]
            else:
                return obj

        report_dict = convert_datetimes(report_dict)

        # Save report to history
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"{Path(filename).stem}_{timestamp}.json"
        result_filepath = os.path.join(app.config['RESULTS_FOLDER'], result_filename)

        with open(result_filepath, 'w') as f:
            json.dump(report_dict, f, indent=2)

        print(f"Saved test result to: {result_filepath}")

        return jsonify({
            'success': True,
            'report': report_dict,
            'filename': filename,
            'result_id': result_filename
        })

    except Exception as e:
        # Log full traceback for debugging
        import traceback
        error_traceback = traceback.format_exc()
        print(f"\n{'='*80}")
        print(f"ERROR processing WAV file:")
        print(error_traceback)
        print(f"{'='*80}\n")

        # Clean up file on error
        try:
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
                print(f"Cleaned up file: {filepath}")
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")

        return jsonify({'error': str(e)}), 500


@app.route('/results/<filename>')
def view_results(filename):
    """Display interactive dashboard for results"""
    return render_template('results.html', filename=filename)


@app.route('/history')
def history():
    """View all test history"""
    # Get all test results
    result_files = glob.glob(os.path.join(app.config['RESULTS_FOLDER'], '*.json'))
    result_files.sort(key=os.path.getmtime, reverse=True)  # Most recent first

    history_list = []
    for filepath in result_files:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                history_list.append({
                    'id': os.path.basename(filepath),
                    'name': data.get('conversation_name', 'Unknown'),
                    'timestamp': data.get('timestamp', ''),
                    'total_errors': data.get('total_errors', 0),
                    'order_status': 'PASSED' if data.get('order_validation', {}).get('is_correct') else 'FAILED'
                })
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            continue

    return render_template('history.html', history=history_list)


@app.route('/api/result/<result_id>')
def get_result(result_id):
    """Get a saved test result by ID"""
    filepath = os.path.join(app.config['RESULTS_FOLDER'], result_id)

    if not os.path.exists(filepath):
        return jsonify({'error': 'Result not found'}), 404

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return jsonify({'success': True, 'report': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reanalyze/<result_id>', methods=['POST'])
def reanalyze_result(result_id):
    """Re-run error detection and order analysis on existing result"""
    filepath = os.path.join(app.config['RESULTS_FOLDER'], result_id)

    if not os.path.exists(filepath):
        return jsonify({'error': 'Result not found'}), 404

    try:
        # Load existing report
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Recreate TestReport from saved data
        from testing_framework.core.test_reporter import TestReport, TurnResult, ConversationUtterance

        report = TestReport(
            conversation_name=data['conversation_name'],
            timestamp=data['timestamp']
        )

        # Reconstruct turns and utterances
        for turn_data in data['turns']:
            utterances = []
            for utt_data in turn_data['utterances']:
                utterance = ConversationUtterance(
                    timestamp_seconds=utt_data['timestamp_seconds'],
                    speaker=utt_data['speaker'],
                    text=utt_data['text']
                )
                utterances.append(utterance)

            turn = TurnResult(
                turn_number=turn_data['turn_number'],
                wav_file=turn_data.get('wav_file', ''),
                utterances=utterances,
                transcription=turn_data.get('transcription', ''),
                bot_response=turn_data.get('bot_response', ''),
                start_time=datetime.now()
            )
            report.turns.append(turn)

        # Run error detection and order analysis
        menu_validator = MenuValidator(MENU)
        error_detector = ErrorDetector(menu_validator)
        order_analyzer = OrderAnalyzer(menu_validator)

        # Reset error tracking
        report.total_errors = 0
        report.error_breakdown = {}

        # Detect errors in each utterance
        for turn_result in report.turns:
            for utterance in turn_result.utterances:
                errors = error_detector.detect_errors(utterance)
                utterance.errors = errors  # Replace old errors

                for error in errors:
                    report.add_error(error.error_type)

        # Extract and validate order
        all_utterances = []
        for turn in report.turns:
            all_utterances.extend(turn.utterances)

        if all_utterances:
            order_summary = order_analyzer.extract_order(all_utterances)
            order_validation = order_analyzer.validate_order(order_summary)

            report.order_summary = order_summary
            report.order_validation = order_validation

        # Convert to dict
        report_dict = asdict(report)

        # Convert order_summary and order_validation to dicts if they exist
        if report.order_summary:
            report_dict['order_summary'] = asdict(report.order_summary)
        if report.order_validation:
            report_dict['order_validation'] = asdict(report.order_validation)

        # Save updated report
        with open(filepath, 'w') as f:
            json.dump(report_dict, f, indent=2)

        print(f"Re-analyzed and saved: {filepath}")

        return jsonify({'success': True, 'report': report_dict})

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"ERROR re-analyzing:\n{error_traceback}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
