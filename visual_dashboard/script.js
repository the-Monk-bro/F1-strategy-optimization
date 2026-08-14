let raceData = [];
let currentRace = null;
let currentAgent = "qrl"; // default to qrl
let currentLapIndex = 0;
let playing = false;
let playInterval;

const TYRE_MAP = {
    0: { name: "Soft", color: "var(--tyre-soft)" },
    1: { name: "Medium", color: "var(--tyre-medium)" },
    2: { name: "Hard", color: "var(--tyre-hard)" },
    3: { name: "Intermediate", color: "var(--tyre-inter)" },
    4: { name: "Wet", color: "var(--tyre-wet)" }
};

document.addEventListener("DOMContentLoaded", async () => {
    // Attempt to load JSON data
    try {
        const response = await fetch('../dashboard/presentation_data.json');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        raceData = data.races;
        populateRaceSelect();
    } catch (error) {
        console.error("Error loading presentation data:", error);
        document.getElementById('strategy-insight').innerHTML = 
            "<span style='color:red;'>Error loading data. Make sure to generate the data first by running <code>generate_presentation_data.py</code>, and serve this folder using a web server (e.g., <code>npx serve</code> or <code>python -m http.server</code>).</span>";
    }

    document.getElementById("btn-play").addEventListener("click", () => {
        if(!playing) {
            startSimulation();
            document.getElementById("btn-play").textContent = "Resume";
        }
    });

    document.getElementById("btn-pause").addEventListener("click", () => {
        playing = false;
        clearInterval(playInterval);
    });

    document.getElementById("btn-reset").addEventListener("click", () => {
        playing = false;
        clearInterval(playInterval);
        document.getElementById("btn-play").textContent = "Play";
        currentLapIndex = 0;
        updateUI();
    });

    document.getElementById("race-select").addEventListener("change", (e) => {
        const idx = e.target.value;
        if (idx !== "") {
            currentRace = raceData[idx];
            document.getElementById("driver-name-display").textContent = currentRace.driver;
            resetSimulation();
        }
    });

    document.getElementById("agent-select").addEventListener("change", (e) => {
        currentAgent = e.target.value;
        const title = currentAgent === "qrl" ? "AI Agent (QRL)" : "AI Agent (DQN)";
        document.getElementById("ai-model-title").textContent = title;
        if (currentRace) {
            resetSimulation();
        }
    });

    document.getElementById("lap-slider").addEventListener("input", (e) => {
        if (!currentRace) return;
        playing = false;
        clearInterval(playInterval);
        document.getElementById("btn-play").textContent = "Play";
        currentLapIndex = parseInt(e.target.value);
        updateUI();
    });
});

function resetSimulation() {
    currentLapIndex = 0;
    playing = false;
    clearInterval(playInterval);
    document.getElementById("btn-play").textContent = "Play";
    drawTrackMarkers();
    updateUI();
}

function drawTrackMarkers() {
    if (!currentRace) return;
    const strategyKey = currentAgent === "qrl" ? "qrl_strategy" : "dqn_strategy";
    const maxLaps = currentRace[strategyKey].length;
    
    const markersContainer = document.getElementById("track-markers");
    markersContainer.innerHTML = ''; // clear existing
    
    // Draw a marker every 10 laps
    const interval = maxLaps > 50 ? 10 : 5;
    
    for (let i = 0; i <= maxLaps; i++) {
        if (i % interval === 0 || i === maxLaps) {
            const marker = document.createElement("div");
            marker.className = "marker";
            
            // The track is drawn such that 100% lap = 80% left + 10 offset (used in updateUI logic)
            // wait, in updateUI: baseProgress = (lap/maxLaps)*80. Then progress = baseProgress + 10.
            // So left percentage is (i/maxLaps * 80) + 10
            
            const leftPct = (i / maxLaps) * 80 + 10;
            marker.style.position = "absolute";
            marker.style.left = `${leftPct}%`;
            
            const label = document.createElement("span");
            label.textContent = `L${i}`;
            marker.appendChild(label);
            
            markersContainer.appendChild(marker);
        }
    }
}

function populateRaceSelect() {
    const select = document.getElementById("race-select");
    select.innerHTML = '<option value="">-- Choose a Race --</option>';
    
    raceData.forEach((race, idx) => {
        const option = document.createElement("option");
        option.value = idx;
        option.textContent = `${race.track} ${race.year} - vs ${race.driver}`;
        select.appendChild(option);
    });

    // Auto-select first if available
    if (raceData.length > 0) {
        select.value = 0;
        select.dispatchEvent(new Event('change'));
    }
}

function startSimulation() {
    if (!currentRace) return;
    playing = true;
    
    const strategyKey = currentAgent === "qrl" ? "qrl_strategy" : "dqn_strategy";
    const maxLaps = currentRace[strategyKey].length;
    
    playInterval = setInterval(() => {
        if (!playing) return;
        
        currentLapIndex++;
        if (currentLapIndex >= maxLaps) {
            playing = false;
            clearInterval(playInterval);
            currentLapIndex = maxLaps - 1; // stay at end
            document.getElementById("btn-play").textContent = "Play";
            showFinalResult();
            return;
        }
        
        updateUI();
    }, calculateSpeed());
}

function calculateSpeed() {
    const speedRange = document.getElementById("speed-range").value;
    // value 1 -> 2000ms, value 10 -> 200ms
    return 2200 - (speedRange * 200);
}

function formatTime(seconds) {
    if(!seconds) return "0.000";
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(3);
    return mins > 0 ? `${mins}:${secs.padStart(6, '0')}` : secs;
}

function updateUI() {
    if (!currentRace) return;
    
    const strategyKey = currentAgent === "qrl" ? "qrl_strategy" : "dqn_strategy";
    const agentLap = currentRace[strategyKey][currentLapIndex];
    const realLap = currentRace.real_strategy[currentLapIndex];
    
    if(!agentLap || !realLap) return;

    const maxLaps = currentRace[strategyKey].length;
    document.getElementById("current-lap").textContent = agentLap.lap;
    document.getElementById("total-laps").textContent = maxLaps;
    
    document.getElementById("lap-slider").max = maxLaps - 1;
    document.getElementById("lap-slider").value = currentLapIndex;

    // Update AI Stats
    updateDriverStats("ai", agentLap);
    // Update Real Stats
    updateDriverStats("real", realLap);

    // Update Positions on Track
    // We visualize this by showing cumulative time. Lower cumulative time = further ahead.
    const maxCumTime = currentRace.real_strategy[maxLaps - 1].cumulative_time;
    
    // Normalize positions between 0 and 100%
    // To make it look like a race, the leader is at 90%, and the follower is trailing
    const timeDiff = realLap.cumulative_time - agentLap.cumulative_time; // Positive means AI is ahead
    
    let agentProgress, realProgress;
    const baseProgress = (agentLap.lap / maxLaps) * 80; // Scale to 80% to leave room for gap visualization
    
    if (timeDiff > 0) {
        // AI ahead
        agentProgress = baseProgress + 10;
        realProgress = baseProgress + 10 - Math.min(10, timeDiff / 5); // visually cap gap
    } else {
        // Real ahead
        realProgress = baseProgress + 10;
        agentProgress = baseProgress + 10 - Math.min(10, Math.abs(timeDiff) / 5);
    }

    document.getElementById("ai-wrapper").style.left = `${agentProgress}%`;
    document.getElementById("real-wrapper").style.left = `${realProgress}%`;

    // Strategy Insight Logic
    let insightHtml = "";
    if (agentLap.tyre_compound !== realLap.tyre_compound) {
        insightHtml = `Strategy Diverged: <span class="highlight-diff">AI is on ${TYRE_MAP[agentLap.tyre_compound].name}</span> while Real Driver is on ${TYRE_MAP[realLap.tyre_compound].name}.`;
    } else {
        insightHtml = "Both drivers are currently on the same compound.";
    }

    if (timeDiff > 0) {
        insightHtml += `<br><br><span class="highlight-win">AI is leading by ${timeDiff.toFixed(2)}s</span>`;
    } else {
        insightHtml += `<br><br>Real Driver is leading by ${Math.abs(timeDiff).toFixed(2)}s`;
    }

    document.getElementById("strategy-insight").innerHTML = insightHtml;
}

function updateDriverStats(prefix, lapData) {
    const tyreInfo = TYRE_MAP[lapData.tyre_compound];
    document.getElementById(`${prefix}-tyre`).innerHTML = `
        <span class="tyre-dot" style="background-color: ${tyreInfo.color}; box-shadow: 0 0 5px ${tyreInfo.color}"></span>
        ${tyreInfo.name}
    `;
    
    // Color the car based on the tyre compound
    const carElem = document.getElementById(`${prefix}-car`);
    if (carElem) {
        carElem.style.background = tyreInfo.color;
        // Adjust text color so it's readable if the tyre color is light
        if (lapData.tyre_compound === 2 || lapData.tyre_compound === 1) { 
            carElem.style.color = '#000'; // Dark text for Hard/Medium
            carElem.style.border = '1px solid #000';
        } else {
            carElem.style.color = '#fff';
            carElem.style.border = `1px solid ${tyreInfo.color}`;
        }
    }
    
    document.getElementById(`${prefix}-age`).textContent = lapData.tyre_age;
    document.getElementById(`${prefix}-lap-time`).textContent = formatTime(lapData.lap_time);
    document.getElementById(`${prefix}-cum-time`).textContent = formatTime(lapData.cumulative_time);

    const pitStatusElem = document.getElementById(`${prefix}-pit-status`);
    if (lapData.pitted) {
        pitStatusElem.textContent = "IN PIT";
    } else {
        pitStatusElem.textContent = "";
    }
}

function showFinalResult() {
    const strategyKey = currentAgent === "qrl" ? "qrl_strategy" : "dqn_strategy";
    const maxLaps = currentRace[strategyKey].length;
    const finalAgent = currentRace[strategyKey][maxLaps - 1];
    const finalReal = currentRace.real_strategy[maxLaps - 1];
    
    const timeDiff = finalReal.cumulative_time - finalAgent.cumulative_time;
    let insightHtml = "<h3>Race Finished!</h3>";
    
    if (timeDiff > 0) {
        insightHtml += `<span class="highlight-win">AI Won!</span> The agent finished ${timeDiff.toFixed(2)} seconds ahead of the real driver.<br>`;
    } else {
        insightHtml += `Real Driver Won by ${Math.abs(timeDiff).toFixed(2)} seconds.<br>`;
    }
    
    insightHtml += `<br><strong>Final Positions:</strong><br>`;
    insightHtml += `AI Agent: P${finalAgent.position}<br>`;
    insightHtml += `Real Driver: P${finalReal.position}`;
    
    document.getElementById("strategy-insight").innerHTML = insightHtml;
}
