/**
 * SRMIST AI Project Duplicate Detector & Entity Resolution
 * Client-Side Interactivity & Live Pre-check Handler
 */

document.addEventListener('DOMContentLoaded', () => {
    initLivePrechecker();
});

function initLivePrechecker() {
    const titleInput = document.getElementById('title');
    const domainInput = document.getElementById('domain');
    const abstractInput = document.getElementById('abstract');
    const fileInput = document.getElementById('proposal_file');
    const btnPrecheck = document.getElementById('btnLivePrecheck');

    if (!titleInput || !btnPrecheck) {
        return;
    }

    let debounceTimer;

    function triggerPrecheck() {
        const title = titleInput.value.trim();
        const domain = domainInput ? domainInput.value.trim() : '';
        const abstract = abstractInput ? abstractInput.value.trim() : '';
        const hasFile = fileInput && fileInput.files && fileInput.files.length > 0;

        if (!title && !abstract && !hasFile) {
            return;
        }

        const indicator = document.getElementById('precheckStatusIndicator');
        if (indicator) {
            indicator.className = 'text-[11px] font-mono px-2 py-0.5 rounded-full bg-sky-100 text-sky-700 font-semibold animate-pulse';
            indicator.innerText = hasFile ? 'Analyzing Document & Text...' : 'Analyzing Vectors...';
        }

        // Use FormData to support uploaded document analysis
        const formData = new FormData();
        formData.append('title', title);
        formData.append('domain', domain);
        formData.append('abstract', abstract);
        if (hasFile) {
            formData.append('proposal_file', fileInput.files[0]);
        }

        fetch('/api/check_similarity', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            renderPrecheckResults(data);
        })
        .catch(err => {
            console.error('Pre-check API error:', err);
            if (indicator) {
                indicator.className = 'text-[11px] font-mono px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 font-semibold';
                indicator.innerText = 'Check Failed';
            }
        });
    }

    btnPrecheck.addEventListener('click', triggerPrecheck);

    if (fileInput) {
        fileInput.addEventListener('change', triggerPrecheck);
    }

    const autoInputs = [titleInput, abstractInput];
    autoInputs.forEach(input => {
        if (input) {
            input.addEventListener('input', () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(triggerPrecheck, 800);
            });
        }
    });
}

function renderPrecheckResults(data) {
    const scoreDisplay = document.getElementById('scoreDisplay');
    const progressBar = document.getElementById('similarityProgressBar');
    const riskBadge = document.getElementById('riskBadgeContainer');
    const matchDetails = document.getElementById('matchDetailsContainer');
    const indicator = document.getElementById('precheckStatusIndicator');
    const entitiesSection = document.getElementById('commonEntitiesSection');
    const entitiesList = document.getElementById('commonEntitiesList');
    const docBadge = document.getElementById('documentAnalysisBadge');
    const docDetails = document.getElementById('documentAnalysisDetails');

    const score = data.max_similarity || 0.0;
    const risk = data.overall_risk;
    const color = data.badge_color;

    // 1. Update indicator
    if (indicator) {
        indicator.className = 'text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold';
        indicator.innerText = 'Analysis Complete';
    }

    // 2. Animate Score Counter
    if (scoreDisplay) {
        scoreDisplay.innerText = score.toFixed(1);
        if (color === 'red') {
            scoreDisplay.className = 'text-5xl font-black text-rose-600 font-mono transition-colors';
        } else if (color === 'amber') {
            scoreDisplay.className = 'text-5xl font-black text-amber-600 font-mono transition-colors';
        } else {
            scoreDisplay.className = 'text-5xl font-black text-emerald-600 font-mono transition-colors';
        }
    }

    // 3. Progress Bar
    if (progressBar) {
        progressBar.style.width = `${Math.min(100, score)}%`;
        if (color === 'red') {
            progressBar.className = 'h-3 rounded-full bg-rose-500 transition-all duration-500';
        } else if (color === 'amber') {
            progressBar.className = 'h-3 rounded-full bg-amber-500 transition-all duration-500';
        } else {
            progressBar.className = 'h-3 rounded-full bg-emerald-500 transition-all duration-500';
        }
    }

    // 4. Alert Badge
    if (riskBadge) {
        if (risk === 'HIGH_DUPLICATE') {
            riskBadge.innerHTML = `
                <div class="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <span>High Duplicate Alert (>80% Match)</span>
                </div>
                <p class="text-[11px] text-rose-600 font-medium mt-1">This proposal will be flagged for review or merged with existing records.</p>
            `;
        } else if (risk === 'MODERATE_OVERLAP') {
            riskBadge.innerHTML = `
                <div class="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
                    <i class="fa-solid fa-circle-exclamation"></i>
                    <span>Moderate Overlap (50-79% Match)</span>
                </div>
                <p class="text-[11px] text-amber-700 font-medium mt-1">Substantial conceptual overlap detected. Review suggested.</p>
            `;
        } else {
            riskBadge.innerHTML = `
                <div class="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                    <i class="fa-solid fa-circle-check"></i>
                    <span>Original Proposal (<50% Overlap)</span>
                </div>
                <p class="text-[11px] text-emerald-700 font-medium mt-1">Idea appears unique and safe for academic submission!</p>
            `;
        }
    }

    // 5. Document analysis feedback
    if (docBadge && docDetails) {
        if (data.file_analyzed) {
            docBadge.classList.remove('hidden');
            docDetails.innerText = `Extracted and evaluated ${data.file_text_words} words from attached document file.`;
        } else {
            docBadge.classList.add('hidden');
        }
    }

    // 6. Closest Match Info
    if (matchDetails) {
        if (data.best_match && score > 20.0) {
            matchDetails.innerHTML = `
                <div class="space-y-1.5">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-slate-800">${data.best_match.title}</span>
                        <span class="font-bold font-mono text-[11px] px-2 py-0.5 rounded ${color === 'red' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'}">${data.best_match.score}%</span>
                    </div>
                    <div class="text-[11px] text-slate-500">
                        Author: <span class="font-semibold text-slate-700">${data.best_match.author}</span> • Domain: <span class="text-sky-600">${data.best_match.domain}</span>
                    </div>
                </div>
            `;
        } else {
            matchDetails.innerHTML = `
                <div class="text-slate-500 text-center py-1">
                    No significant conceptual duplicates detected in the database.
                </div>
            `;
        }
    }

    // 7. Extracted Entities
    if (entitiesSection && entitiesList) {
        if (data.best_match && data.best_match.common_entities && data.best_match.common_entities.length > 0) {
            entitiesSection.classList.remove('hidden');
            entitiesList.innerHTML = data.best_match.common_entities.map(e => `
                <span class="px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-200 text-[10px] font-mono font-semibold">${e}</span>
            `).join('');
        } else {
            entitiesSection.classList.add('hidden');
        }
    }
}
