/**
 * Dashboard JavaScript for Test Results Visualization
 * Renders interactive dashboard with charts, timelines, and error analysis
 */

// Store current report globally for tab switching
let currentReport = null;
let currentEngine = 'primary'; // Default to primary engine

function renderDashboard(report) {
    currentReport = report;

    // Set filename
    document.getElementById('filename').textContent = report.conversation_name;

    // Summary cards
    const totalUtterances = report.turns.reduce((sum, turn) => sum + turn.utterances.length, 0);
    document.getElementById('totalUtterances').textContent = totalUtterances;
    document.getElementById('totalErrors').textContent = report.total_errors;
    document.getElementById('duration').textContent = formatDuration(report.total_duration_seconds);

    // Order status
    if (report.order_validation) {
        const status = report.order_validation.is_correct ? 'PASSED ✓' : 'FAILED ✗';
        const statusClass = report.order_validation.is_correct ? 'success' : 'error';
        document.getElementById('orderStatus').innerHTML = `<span class="${statusClass}">${status}</span>`;
        document.getElementById('orderAnalysisSection').style.display = 'block';
    } else {
        document.getElementById('orderStatus').textContent = 'N/A';
    }

    // Error breakdown chart (only show if there are errors)
    if (report.error_breakdown && Object.keys(report.error_breakdown).length > 0) {
        document.getElementById('errorChartSection').style.display = 'block';
        renderErrorChart(report.error_breakdown);
    }

    // Render keywords debug info if available
    renderKeywordsDebug(report);

    // Setup audio player
    setupAudioPlayer(report);

    // Render engine tabs if multiple engines available
    renderEngineTabs(report);

    // Timeline - show primary with errors, or first engine if multiple
    if (report.engine_results && Object.keys(report.engine_results).length > 1) {
        // Multiple engines - show first engine's raw data
        const firstEngine = Object.keys(report.engine_results)[0];
        renderTimelineFromEngine(report.engine_results[firstEngine], firstEngine);
    } else {
        // Single engine or no engine data - show primary with error annotations
        renderTimeline(report.turns, 'primary');
    }

    // Error details (only show if there are errors)
    const hasErrors = report.turns.some(turn =>
        turn.utterances.some(utt => utt.errors && utt.errors.length > 0)
    );
    if (hasErrors) {
        document.getElementById('errorDetailsSection').style.display = 'block';
        renderErrorDetails(report.turns);
    }

    // Order analysis
    if (report.order_summary && report.order_summary.items && report.order_summary.items.length > 0) {
        renderOrderAnalysis(report.order_summary, report.order_validation);
    }

    // Collapsible sections
    setupCollapsibles();
}

function renderErrorChart(errorBreakdown) {
    const ctx = document.getElementById('errorChart').getContext('2d');
    const labels = Object.keys(errorBreakdown);
    const data = Object.values(errorBreakdown);

    // Color palette for error types
    const colors = [
        'rgba(255, 99, 132, 0.7)',
        'rgba(255, 159, 64, 0.7)',
        'rgba(255, 205, 86, 0.7)',
        'rgba(75, 192, 192, 0.7)',
        'rgba(153, 102, 255, 0.7)'
    ];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Error Count',
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderColor: colors.slice(0, labels.length).map(c => c.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Error Distribution'
                }
            }
        }
    });
}

function setupAudioPlayer(report) {
    // Setup audio player with the WAV file
    const audioSection = document.getElementById('audioPlayerSection');
    const audioPlayer = document.getElementById('audioPlayer');
    const audioSource = document.getElementById('audioSource');

    if (report.conversation_name) {
        // Construct audio file path (assuming it's in static/uploads)
        const audioPath = `/static/uploads/${report.conversation_name}.wav`;
        audioSource.src = audioPath;
        audioPlayer.load();
        audioSection.style.display = 'block';
    }
}

function playAudioAt(timestamp) {
    // Play audio from specific timestamp
    const audioPlayer = document.getElementById('audioPlayer');
    if (audioPlayer) {
        audioPlayer.currentTime = timestamp;
        audioPlayer.play();
    }
}

function renderKeywordsDebug(report) {
    // Check if we have engine results with keyword metadata
    if (!report.engine_results) return;

    let keywordInfo = null;
    let engineName = null;

    // Find Deepgram engine with keyword metadata
    for (const [name, result] of Object.entries(report.engine_results)) {
        if (result.metadata && result.metadata.keywords_count) {
            keywordInfo = result.metadata;
            engineName = name;
            break;
        }
    }

    if (!keywordInfo) return; // No keyword metadata found

    // Show the debug section
    document.getElementById('keywordsDebugSection').style.display = 'block';

    const debugDiv = document.getElementById('keywordsDebug');
    const keywordsList = keywordInfo.keywords_sent || [];
    const first10 = keywordsList.slice(0, 10);
    const remaining = keywordsList.length - 10;

    // Show phonetic corrections if available
    const corrections = keywordInfo.phonetic_corrections || [];
    const correctionsHtml = corrections.length > 0 ? `
        <div style="margin-top: 20px; padding: 15px; background: #d1fae5; border-left: 3px solid #10b981; border-radius: 3px;">
            <strong>✅ Phonetic Corrections Applied: ${corrections.length}</strong>
            <div style="margin-top: 10px; max-height: 200px; overflow-y: auto;">
                ${corrections.map((c, i) => `
                    <div style="margin: 8px 0; padding: 8px; background: white; border-radius: 3px;">
                        <div><strong>#${i + 1}</strong> @ ${c.timestamp.toFixed(2)}s</div>
                        <div style="color: #dc2626;">❌ <del>${c.original}</del></div>
                        <div style="color: #059669;">✓ ${c.corrected}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    ` : `
        <div style="margin-top: 20px; padding: 15px; background: #fef3c7; border-left: 3px solid #f59e0b; border-radius: 3px;">
            <strong>⚠️ No Phonetic Corrections Applied</strong><br>
            No known mis-transcriptions were detected in this audio.
        </div>
    `;

    debugDiv.innerHTML = `
        <div style="margin-bottom: 15px;">
            <strong>🎯 Keyword Boosting Status:</strong> <span style="color: green; font-weight: bold;">ENABLED</span>
        </div>
        <div style="margin-bottom: 10px;">
            <strong>Engine:</strong> ${engineName}<br>
            <strong>Keywords Sent:</strong> ${keywordInfo.keywords_count} keywords<br>
            <strong>Boost Intensity:</strong> ${keywordInfo.keywords_intensity} / 4 (Strong)<br>
            <strong>Corrections Made:</strong> ${corrections.length} phonetic fixes<br>
        </div>
        <div style="margin-top: 15px;">
            <strong>First 10 Keywords Sent to Deepgram:</strong>
            <div style="background: white; padding: 10px; margin-top: 5px; border-radius: 3px; max-height: 150px; overflow-y: auto;">
                ${first10.map((kw, i) => `<div>${i + 1}. ${kw}:${keywordInfo.keywords_intensity}</div>`).join('')}
                ${remaining > 0 ? `<div style="margin-top: 10px; color: #666;"><em>... and ${remaining} more keywords</em></div>` : ''}
            </div>
        </div>
        ${correctionsHtml}
        <div style="margin-top: 15px; padding: 10px; background: #fffbea; border-left: 3px solid #f59e0b; border-radius: 3px;">
            <strong>💡 How it works:</strong><br>
            1. Deepgram receives audio + keyword hints (with intensity:3)<br>
            2. After transcription, phonetic resolver fixes known mis-transcriptions<br>
            3. "gel crazy" → "Jalfrezi", "dopey aza" → "Dopiaza", etc.
        </div>
    `;
}

function renderEngineTabs(report) {
    const tabsContainer = document.getElementById('engineTabs');
    if (!tabsContainer) return;

    tabsContainer.innerHTML = '';

    // Check if we have engine results
    if (!report.engine_results || Object.keys(report.engine_results).length === 0) {
        tabsContainer.style.display = 'none';
        return;
    }

    const engineNames = Object.keys(report.engine_results);

    // Only show tabs if we have multiple engines
    if (engineNames.length === 1) {
        tabsContainer.style.display = 'none';
        return;
    }

    tabsContainer.style.display = 'flex';

    // Add tab for each engine
    let isFirst = true;
    for (const engineName in report.engine_results) {
        const tab = document.createElement('button');
        tab.className = isFirst ? 'engine-tab active' : 'engine-tab';
        tab.textContent = engineName;
        tab.onclick = () => switchEngine(engineName);
        tabsContainer.appendChild(tab);

        if (isFirst) {
            currentEngine = engineName; // Set first engine as current
            isFirst = false;
        }
    }

    // Add diff view tab if multiple engines
    const diffTab = document.createElement('button');
    diffTab.className = 'engine-tab diff-tab';
    diffTab.textContent = '🔄 Compare';
    diffTab.onclick = () => switchEngine('diff');
    tabsContainer.appendChild(diffTab);
}

function switchEngine(engineName) {
    currentEngine = engineName;

    // Update tab active state
    const tabs = document.querySelectorAll('.engine-tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        if (
            (engineName === 'diff' && tab.textContent.includes('Compare')) ||
            tab.textContent === engineName
        ) {
            tab.classList.add('active');
        }
    });

    // Render timeline based on selected engine
    if (engineName === 'diff') {
        renderDiffView(currentReport);
    } else if (currentReport.engine_results && currentReport.engine_results[engineName]) {
        renderTimelineFromEngine(currentReport.engine_results[engineName], engineName);
    } else {
        // Fallback to primary if engine not found
        renderTimeline(currentReport.turns, 'primary');
    }
}

function renderTimeline(turns, engineName = 'primary') {
    const timeline = document.getElementById('timeline');
    timeline.innerHTML = '';

    turns.forEach(turn => {
        turn.utterances.forEach(utterance => {
            const div = document.createElement('div');

            // Add speaker-based color coding
            const speakerClass = getSpeakerClass(utterance.speaker);
            div.className = `utterance ${speakerClass}`;

            const timestamp = document.createElement('span');
            timestamp.className = 'timestamp';
            timestamp.textContent = `[${utterance.timestamp_formatted}]`;

            const speaker = document.createElement('span');
            speaker.className = 'speaker';
            speaker.textContent = utterance.speaker;

            const text = document.createElement('span');
            text.className = 'text';
            text.textContent = utterance.text;

            // Make utterance clickable to play audio
            div.style.cursor = 'pointer';
            div.title = 'Click to play audio from this moment';
            div.onclick = () => playAudioAt(utterance.timestamp_seconds);

            div.appendChild(timestamp);
            div.appendChild(speaker);
            div.appendChild(text);

            // Add error badges (only for primary engine)
            if (engineName === 'primary' && utterance.errors && utterance.errors.length > 0) {
                div.classList.add('has-errors');
                utterance.errors.forEach(error => {
                    const badge = document.createElement('span');
                    badge.className = `error-badge ${error.severity.toLowerCase()}`;
                    badge.textContent = error.error_type;

                    // Build tooltip text
                    let tooltipText = error.message;
                    if (error.suggestion) {
                        tooltipText += `\n💡 Suggestion: ${error.suggestion}`;
                    }
                    badge.title = tooltipText;

                    div.appendChild(badge);
                });
            }

            timeline.appendChild(div);
        });
    });
}

function renderTimelineFromEngine(engineResult, engineName) {
    const timeline = document.getElementById('timeline');
    timeline.innerHTML = '';

    if (!engineResult || !engineResult.utterances) {
        timeline.innerHTML = '<p class="error">No utterances found for this engine</p>';
        return;
    }

    engineResult.utterances.forEach(utterance => {
        const div = document.createElement('div');

        // Add speaker-based color coding
        const speakerClass = getSpeakerClass(utterance.speaker);
        div.className = `utterance ${speakerClass}`;

        const timestamp = document.createElement('span');
        timestamp.className = 'timestamp';
        timestamp.textContent = `[${formatTimestamp(utterance.timestamp_seconds)}]`;

        const speaker = document.createElement('span');
        speaker.className = 'speaker';
        speaker.textContent = utterance.speaker;

        const text = document.createElement('span');
        text.className = 'text';
        text.textContent = utterance.text;

        // Make utterance clickable to play audio
        div.style.cursor = 'pointer';
        div.title = 'Click to play audio from this moment';
        div.onclick = () => playAudioAt(utterance.timestamp_seconds);

        div.appendChild(timestamp);
        div.appendChild(speaker);
        div.appendChild(text);

        timeline.appendChild(div);
    });
}

function renderDiffView(report) {
    const timeline = document.getElementById('timeline');
    timeline.innerHTML = '';

    // Get engines to compare (first two)
    const engineNames = Object.keys(report.engine_results);
    if (engineNames.length < 2) {
        timeline.innerHTML = '<p class="error">Need at least 2 engines for comparison</p>';
        return;
    }

    const engine1Name = engineNames[0];
    const engine2Name = engineNames[1];
    const engine1 = report.engine_results[engine1Name];
    const engine2 = report.engine_results[engine2Name];

    // Create side-by-side comparison with utterances
    const comparisonContainer = document.createElement('div');
    comparisonContainer.className = 'diff-container';

    const leftColumn = document.createElement('div');
    leftColumn.className = 'diff-column';
    leftColumn.innerHTML = `<h3>${engine1Name} (${engine1.utterances.length} utterances)</h3>`;

    const rightColumn = document.createElement('div');
    rightColumn.className = 'diff-column';
    rightColumn.innerHTML = `<h3>${engine2Name} (${engine2.utterances.length} utterances)</h3>`;

    // Render utterances side by side
    const leftUtterances = document.createElement('div');
    leftUtterances.className = 'diff-utterances';

    const rightUtterances = document.createElement('div');
    rightUtterances.className = 'diff-utterances';

    // Get max utterance count
    const maxCount = Math.max(engine1.utterances.length, engine2.utterances.length);

    for (let i = 0; i < maxCount; i++) {
        // Left utterance
        if (i < engine1.utterances.length) {
            const utt = engine1.utterances[i];
            const uttDiv = createDiffUtterance(utt, i);
            leftUtterances.appendChild(uttDiv);
        } else {
            leftUtterances.appendChild(createEmptyUtterance());
        }

        // Right utterance
        if (i < engine2.utterances.length) {
            const utt = engine2.utterances[i];
            const uttDiv = createDiffUtterance(utt, i);
            rightUtterances.appendChild(uttDiv);
        } else {
            rightUtterances.appendChild(createEmptyUtterance());
        }
    }

    leftColumn.appendChild(leftUtterances);
    rightColumn.appendChild(rightUtterances);

    comparisonContainer.appendChild(leftColumn);
    comparisonContainer.appendChild(rightColumn);

    timeline.appendChild(comparisonContainer);
}

function createDiffUtterance(utterance, index) {
    const div = document.createElement('div');
    const speakerClass = getSpeakerClass(utterance.speaker);
    div.className = `diff-utterance ${speakerClass}`;

    const timestamp = document.createElement('span');
    timestamp.className = 'timestamp';
    timestamp.textContent = `[${formatTimestamp(utterance.timestamp_seconds)}]`;

    const speaker = document.createElement('span');
    speaker.className = 'speaker';
    speaker.textContent = utterance.speaker;

    const text = document.createElement('span');
    text.className = 'text';
    text.textContent = utterance.text;

    div.appendChild(timestamp);
    div.appendChild(speaker);
    div.appendChild(text);

    return div;
}

function createEmptyUtterance() {
    const div = document.createElement('div');
    div.className = 'diff-utterance empty';
    div.innerHTML = '<span class="text">(no utterance)</span>';
    return div;
}

function getSpeakerClass(speaker) {
    // Normalize speaker labels and assign colors
    const normalized = speaker.toLowerCase();
    if (normalized.includes('speaker_0') || normalized.includes('user') || normalized.includes('customer')) {
        return 'speaker-0';
    } else if (normalized.includes('speaker_1') || normalized.includes('bot') || normalized.includes('agent')) {
        return 'speaker-1';
    } else if (normalized.includes('speaker_2')) {
        return 'speaker-2';
    }
    return 'speaker-default';
}

function formatTimestamp(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function renderErrorDetails(turns) {
    const container = document.getElementById('errorDetails');
    container.innerHTML = '';

    const allErrors = [];
    turns.forEach(turn => {
        turn.utterances.forEach(utterance => {
            if (utterance.errors && utterance.errors.length > 0) {
                utterance.errors.forEach(error => {
                    allErrors.push({
                        timestamp: utterance.timestamp_formatted,
                        speaker: utterance.speaker,
                        text: utterance.text,
                        error: error
                    });
                });
            }
        });
    });

    if (allErrors.length === 0) {
        container.innerHTML = '<p class="success">No errors detected! 🎉</p>';
        return;
    }

    const list = document.createElement('ul');
    list.className = 'error-list';

    allErrors.forEach(item => {
        const li = document.createElement('li');

        const severityClass = item.error.severity.toLowerCase();
        const severityIcon = item.error.severity === 'ERROR' ? '❌' : '⚠️';

        li.innerHTML = `
            <div class="error-item ${severityClass}">
                <div class="error-header">
                    <strong>[${item.timestamp}] ${item.speaker}</strong>
                    <span class="error-badge-detail ${severityClass}">${severityIcon} ${item.error.error_type}</span>
                </div>
                <div class="error-text">"${item.text}"</div>
                <div class="error-message">${item.error.message}</div>
                ${item.error.suggestion ? `<div class="suggestion">💡 <strong>Suggestion:</strong> ${item.error.suggestion}</div>` : ''}
            </div>
        `;
        list.appendChild(li);
    });

    container.appendChild(list);
}

function renderOrderAnalysis(orderSummary, orderValidation) {
    const container = document.getElementById('orderAnalysis');
    container.innerHTML = '';

    // Extracted Order Table
    let html = '<h3>Extracted Order</h3>';
    html += '<table class="order-table">';
    html += '<tr><th>Item</th><th>Qty</th><th>Unit Price</th><th>Total</th><th>Status</th></tr>';

    orderSummary.items.forEach(item => {
        const validClass = item.is_valid ? '' : 'invalid';
        const statusIcon = item.is_valid ? '✅' : '❌';
        html += `
            <tr class="${validClass}">
                <td>${item.name}</td>
                <td>${item.quantity}</td>
                <td>£${item.unit_price.toFixed(2)}</td>
                <td>£${item.total_price.toFixed(2)}</td>
                <td>${statusIcon}</td>
            </tr>
        `;
    });

    html += '</table>';

    // Validation Summary
    html += '<div class="order-summary">';
    html += `<p><strong>Calculated Total:</strong> £${orderSummary.calculated_total.toFixed(2)}</p>`;
    html += `<p><strong>Bot Stated Total:</strong> £${orderSummary.stated_total ? orderSummary.stated_total.toFixed(2) : 'N/A'}</p>`;

    if (orderValidation) {
        if (Math.abs(orderValidation.price_difference) > 0.01) {
            const diffSign = orderValidation.price_difference > 0 ? '+' : '';
            html += `<p class="error"><strong>Difference:</strong> ${diffSign}£${orderValidation.price_difference.toFixed(2)} ❌</p>`;
        }

        if (orderValidation.errors && orderValidation.errors.length > 0) {
            html += '<h4>Issues Found:</h4><ul class="validation-errors">';
            orderValidation.errors.forEach(error => {
                html += `<li class="error">${error}</li>`;
            });
            html += '</ul>';
        }

        const statusIcon = orderValidation.is_correct ? '✅' : '❌';
        const statusClass = orderValidation.is_correct ? 'success' : 'error';
        html += `<p class="validation-status ${statusClass}"><strong>Validation Status:</strong> ${statusIcon} ${orderValidation.is_correct ? 'PASSED' : 'FAILED'}</p>`;
    }

    html += '</div>';
    container.innerHTML = html;
}

function setupCollapsibles() {
    const collapsibles = document.querySelectorAll('.collapsible');
    collapsibles.forEach(header => {
        header.addEventListener('click', () => {
            header.classList.toggle('active');
            const content = header.nextElementSibling;
            const toggle = header.querySelector('.toggle');

            if (content.style.display === 'none' || content.style.display === '') {
                content.style.display = 'block';
                toggle.textContent = '▲';
            } else {
                content.style.display = 'none';
                toggle.textContent = '▼';
            }
        });
    });
}

function formatDuration(seconds) {
    if (seconds === 0 || seconds === undefined) {
        return '0:00';
    }
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}
