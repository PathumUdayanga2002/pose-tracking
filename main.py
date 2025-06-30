from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Create a static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse('index.html')

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Pose Tracking</title>
        <script src=\"https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.18.0/dist/tf.min.js\"></script>
        <script src=\"https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469242/pose.js\"></script>
        <script src=\"https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils@0.5.1675469242/drawing_utils.js\"></script>
        <script src=\"https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js\"></script>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            
            h1 {
                text-align: center;
                color: #2c3e50;
                margin-bottom: 20px;
            }
            
            .container {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .video-container {
                position: relative;
                width: 640px;
                height: 480px;
            }
            
            #video, #output { 
                position: absolute; 
                top: 0; 
                left: 0; 
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            }
            
            #output { 
                z-index: 10; 
                pointer-events: none; 
            }
            
            #feedback { 
                position: absolute; 
                top: 10px; 
                left: 10px; 
                font-size: 1.5em; 
                color: green; 
                z-index: 20; 
                background-color: rgba(255, 255, 255, 0.7);
                padding: 5px 10px;
                border-radius: 5px;
                max-width: 80%;
                text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.1);
            }
            
            .stats-container {
                display: flex;
                flex-direction: column;
                gap: 20px;
                width: 400px;
            }
            
            #chart-container { 
                width: 100%;
                height: 320px; 
                background: #fff; 
                border-radius: 10px; 
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); 
                padding: 15px;
                box-sizing: border-box;
                display: none;
            }
            
            #stats { 
                width: 100%;
                font-size: 1em; 
                background: #fff; 
                border-radius: 10px; 
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); 
                padding: 15px; 
                box-sizing: border-box;
                display: none;
                line-height: 1.5;
            }
            
            #stats h3 {
                color: #2c3e50;
                border-bottom: 1px solid #eee;
                padding-bottom: 5px;
            }
            
            #stats ul li {
                margin-bottom: 5px;
            }
            
            @media (max-width: 1100px) {
                .container {
                    flex-direction: column;
                    align-items: center;
                }
                
                .stats-container {
                    width: 640px;
                }
            }
        </style>
    </head>
    <body>
        <h1>Real-time Pose Tracking for Presentation Practice</h1>
        
        <div class=\"container\">
            <div class=\"video-container\">
                <video id=\"video\" width=\"640\" height=\"480\" autoplay muted playsinline style=\"display:none;\"></video>
                <canvas id=\"output\" width=\"640\" height=\"480\"></canvas>
                <div id=\"feedback\"></div>
            </div>
            
            <div class=\"stats-container\">
                <div id=\"chart-container\">
                    <canvas id=\"piechart\"></canvas>
                </div>
                <div id=\"stats\"></div>
                
                <div id=\"history-container\" style=\"background: #fff; border-radius: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); padding: 15px; box-sizing: border-box;\">
                    <h3 style=\"color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5px;\">Your Progress</h3>
                    <p>Practice regularly to see your improvement over time. The application tracks your progress across sessions.</p>
                    <div id=\"progress-stats\">
                        <p>Sessions completed: <span id=\"sessions-count\">0</span></p>
                        <p>Total practice time: <span id=\"total-practice-time\">0</span> minutes</p>
                    </div>
                </div>
            </div>
        </div>
        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('output');
            const ctx = canvas.getContext('2d');
            const feedbackDiv = document.getElementById('feedback');
            const chartContainer = document.getElementById('chart-container');
            const statsDiv = document.getElementById('stats');
            const sessionsCountElement = document.getElementById('sessions-count');
            const totalPracticeTimeElement = document.getElementById('total-practice-time');
            
            // Tracking variables
            let correctFrames = 0, incorrectFrames = 0, totalFrames = 0;
            let correctTime = 0, incorrectTime = 0;
            let lastChartTime = Date.now();
            let pieChart = null;
            
            // Load progress data from localStorage
            let progressData = {
                sessionsCompleted: 0,
                totalPracticeTime: 0 // in minutes
            };
            
            // Try to load existing progress data
            try {
                const savedProgressData = localStorage.getItem('presentationProgressData');
                if (savedProgressData) {
                    progressData = JSON.parse(savedProgressData);
                }
                
                // Update UI with loaded data
                updateProgressDisplay();
            } catch (e) {
                console.error('Error loading progress data:', e);
            }
            
            // Function to update progress display
            function updateProgressDisplay() {
                sessionsCountElement.textContent = progressData.sessionsCompleted;
                totalPracticeTimeElement.textContent = progressData.totalPracticeTime.toFixed(1);
            }

            async function setupCamera() {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                video.srcObject = stream;
                return new Promise((resolve) => {
                    video.onloadedmetadata = () => { resolve(video); };
                });
            }

            function calculateAngle(a, b, c) {
                // a, b, c are {x, y}
                const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
                let angle = Math.abs(radians * 180.0 / Math.PI);
                if (angle > 180) angle = 360 - angle;
                return angle;
            }

            function isBodyLanguageCorrect(lm) {
                // Comprehensive rules for correct presentation body language:
                // 1. Standing upright: shoulders and hips aligned vertically
                // 2. Arms positioned appropriately (not crossed, good gesturing position)
                // 3. Head facing forward
                // 4. No slouching (back straight)
                // 5. Weight balanced on both feet
                // 6. Proper hand gestures (not hidden, not fidgeting)
                // 7. Shoulders relaxed, not hunched
                
                // Check if key landmarks are detected
                if (!lm[11] || !lm[12] || !lm[23] || !lm[24] || !lm[0] || !lm[15] || !lm[16] || !lm[27] || !lm[28]) {
                    return { isCorrect: false, feedback: "Move fully into camera view" };
                }
                
                // Extract key landmarks
                const nose = lm[0];
                const leftShoulder = lm[11], rightShoulder = lm[12];
                const leftElbow = lm[13], rightElbow = lm[14];
                const leftWrist = lm[15], rightWrist = lm[16];
                const leftHip = lm[23], rightHip = lm[24];
                const leftKnee = lm[25], rightKnee = lm[26];
                const leftAnkle = lm[27], rightAnkle = lm[28];
                
                // Calculate midpoints
                const shoulderMidX = (leftShoulder.x + rightShoulder.x) / 2;
                const hipMidX = (leftHip.x + rightHip.x) / 2;
                
                // 1. Posture checks
                const shouldersAligned = Math.abs(leftShoulder.y - rightShoulder.y) < 0.08;
                const hipsAligned = Math.abs(leftHip.y - rightHip.y) < 0.08;
                const backStraight = Math.abs(shoulderMidX - hipMidX) < 0.08;
                
                // 2. Head position
                const headCentered = (nose.x > Math.min(leftShoulder.x, rightShoulder.x)) && 
                                    (nose.x < Math.max(leftShoulder.x, rightShoulder.x));
                const headUpright = nose.y < Math.min(leftShoulder.y, rightShoulder.y);
                
                // 3. Arm position
                const armsNotCrossed = Math.abs(leftWrist.x - rightWrist.x) > 0.15;
                const armsInGesturingPosition = (leftWrist.y > leftElbow.y) && (rightWrist.y > rightElbow.y) && 
                                               (leftWrist.y < leftHip.y) && (rightWrist.y < rightHip.y);
                
                // 4. Weight distribution
                const weightBalanced = Math.abs(leftAnkle.y - rightAnkle.y) < 0.05 && 
                                      Math.abs(leftKnee.y - rightKnee.y) < 0.05;
                
                // 5. Shoulder relaxation
                const shouldersRelaxed = (leftShoulder.y < leftElbow.y) && (rightShoulder.y < rightElbow.y);
                
                // Compile feedback
                let feedbackItems = [];
                if (!shouldersAligned || !shouldersRelaxed) feedbackItems.push("Relax and level your shoulders");
                if (!hipsAligned || !weightBalanced) feedbackItems.push("Balance your weight evenly");
                if (!backStraight) feedbackItems.push("Stand up straight");
                if (!headCentered || !headUpright) feedbackItems.push("Center your head and look forward");
                if (!armsNotCrossed) feedbackItems.push("Uncross your arms");
                if (!armsInGesturingPosition) feedbackItems.push("Position arms for natural gesturing");
                
                // Overall assessment
                const isCorrect = shouldersAligned && hipsAligned && backStraight && 
                                 headCentered && headUpright && armsNotCrossed && 
                                 armsInGesturingPosition && weightBalanced && shouldersRelaxed;
                
                return { 
                    isCorrect: isCorrect, 
                    feedback: isCorrect ? "Great presentation posture!" : feedbackItems.join(" & ")
                };
            }

            async function main() {
                await setupCamera();
                video.play();

                const poseInstance = new pose.Pose({
                    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469242/${file}`
                });
                poseInstance.setOptions({
                    modelComplexity: 1,
                    smoothLandmarks: true,
                    enableSegmentation: false,
                    minDetectionConfidence: 0.5,
                    minTrackingConfidence: 0.5
                });

                poseInstance.onResults(onResults);

                async function detect() {
                    await poseInstance.send({image: video});
                    requestAnimationFrame(detect);
                }
                detect();
            }

            // Store session history for tracking improvement over time
            let sessionHistory = [];
            let sessionStartTime = Date.now();
            
            function onResults(results) {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);
                
                if (results.poseLandmarks) {
                    // Draw pose landmarks
                    window.drawConnectors(ctx, results.poseLandmarks, pose.POSE_CONNECTIONS, {color: '#00FF00', lineWidth: 4});
                    window.drawLandmarks(ctx, results.poseLandmarks, {color: '#FF0000', lineWidth: 2});
                    
                    // Check body language with detailed feedback
                    const lm = results.poseLandmarks;
                    const bodyLanguageResult = isBodyLanguageCorrect(lm);
                    
                    if (bodyLanguageResult.isCorrect) {
                        feedbackDiv.style.color = 'green';
                        correctFrames++;
                    } else {
                        feedbackDiv.style.color = 'red';
                        incorrectFrames++;
                    }
                    
                    feedbackDiv.textContent = bodyLanguageResult.feedback;
                    totalFrames++;
                    
                    // Draw specific feedback annotations on the canvas
                    drawBodyLanguageFeedback(ctx, results.poseLandmarks, bodyLanguageResult);
                } else {
                    feedbackDiv.textContent = 'No pose detected';
                }
                
                // Every 5 minutes (300000 ms), show pie chart and stats
                const now = Date.now();
                if (now - lastChartTime > 300000 && totalFrames > 0) {
                    // Calculate time in seconds (assuming ~30 FPS)
                    correctTime = correctFrames * (1/30);
                    incorrectTime = incorrectFrames * (1/30);
                    
                    // Store session data for tracking improvement
                    const sessionData = {
                        timestamp: now,
                        correctPercentage: (correctFrames / totalFrames) * 100,
                        correctTime: correctTime,
                        incorrectTime: incorrectTime,
                        totalTime: correctTime + incorrectTime
                    };
                    sessionHistory.push(sessionData);
                    
                    // Save session history to localStorage for persistence
                    localStorage.setItem('presentationSessionHistory', JSON.stringify(sessionHistory));
                    
                    // Show updated pie chart and stats
                    showPieChart();
                    lastChartTime = now;
                }
            }
            
            // Function to draw specific feedback on the canvas
            function drawBodyLanguageFeedback(ctx, landmarks, bodyLanguageResult) {
                if (!bodyLanguageResult.isCorrect) {
                    // Draw feedback indicators based on specific issues
                    const feedback = bodyLanguageResult.feedback;
                    
                    // Highlight problematic areas with colored circles
                    if (feedback.includes("shoulders")) {
                        highlightLandmarks(ctx, [landmarks[11], landmarks[12]], 'yellow');
                    }
                    
                    if (feedback.includes("straight") || feedback.includes("posture")) {
                        // Draw line from shoulders to hips to show alignment
                        const shoulderMidX = (landmarks[11].x + landmarks[12].x) / 2;
                        const shoulderMidY = (landmarks[11].y + landmarks[12].y) / 2;
                        const hipMidX = (landmarks[23].x + landmarks[24].x) / 2;
                        const hipMidY = (landmarks[23].y + landmarks[24].y) / 2;
                        
                        ctx.beginPath();
                        ctx.moveTo(shoulderMidX * canvas.width, shoulderMidY * canvas.height);
                        ctx.lineTo(hipMidX * canvas.width, hipMidY * canvas.height);
                        ctx.strokeStyle = 'yellow';
                        ctx.lineWidth = 3;
                        ctx.stroke();
                    }
                    
                    if (feedback.includes("arms")) {
                        highlightLandmarks(ctx, [landmarks[13], landmarks[14], landmarks[15], landmarks[16]], 'orange');
                    }
                    
                    if (feedback.includes("head")) {
                        highlightLandmarks(ctx, [landmarks[0]], 'cyan');
                    }
                    
                    if (feedback.includes("weight") || feedback.includes("balance")) {
                        highlightLandmarks(ctx, [landmarks[27], landmarks[28]], 'magenta');
                    }
                }
            }
            
            // Helper function to highlight specific landmarks
            function highlightLandmarks(ctx, landmarkArray, color) {
                landmarkArray.forEach(landmark => {
                    ctx.beginPath();
                    ctx.arc(landmark.x * canvas.width, landmark.y * canvas.height, 15, 0, 2 * Math.PI);
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 3;
                    ctx.stroke();
                });
            }

            function showPieChart() {
                chartContainer.style.display = 'block';
                statsDiv.style.display = 'block';
                
                // Calculate percentages for pie chart
                const correctPercentage = (correctFrames / totalFrames) * 100;
                const incorrectPercentage = (incorrectFrames / totalFrames) * 100;
                
                // Create pie chart data
                const data = {
                    labels: ['Correct Posture', 'Incorrect Posture'],
                    datasets: [{
                        data: [correctPercentage, incorrectPercentage],
                        backgroundColor: ['#4caf50', '#f44336'],
                    }]
                };
                
                // Update or create pie chart
                if (pieChart) pieChart.destroy();
                pieChart = new Chart(document.getElementById('piechart'), {
                    type: 'pie',
                    data: data,
                    options: {
                        plugins: {
                            legend: { display: true, position: 'bottom' },
                            title: { display: true, text: 'Body Language Analysis (last 5 min)' },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return `${context.label}: ${context.raw.toFixed(1)}%`;
                                    }
                                }
                            }
                        },
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
                
                // Load previous session data from localStorage
                let previousSessions = [];
                try {
                    const savedData = localStorage.getItem('presentationSessionHistory');
                    if (savedData) {
                        previousSessions = JSON.parse(savedData);
                    }
                } catch (e) {
                    console.error('Error loading previous session data:', e);
                }
                
                // Calculate improvement metrics
                let improvementText = '';
                if (previousSessions.length > 1) {
                    const currentSession = previousSessions[previousSessions.length - 1];
                    const previousSession = previousSessions[previousSessions.length - 2];
                    
                    const percentageChange = currentSession.correctPercentage - previousSession.correctPercentage;
                    const improvementDirection = percentageChange >= 0 ? 'improved' : 'decreased';
                    
                    improvementText = `<div style="margin-top: 10px; padding: 8px; background: ${percentageChange >= 0 ? '#e8f5e9' : '#ffebee'}; border-radius: 5px;">
                        <b>Improvement:</b> Your correct posture has ${improvementDirection} by ${Math.abs(percentageChange).toFixed(1)}% since last session
                    </div>`;
                }
                
                // Update stats display with detailed information
                statsDiv.innerHTML = `
                    <div style="margin-bottom: 10px;">
                        <h3 style="margin: 5px 0;">Current Session (5 min)</h3>
                        <div><b>Correct posture:</b> ${correctTime.toFixed(1)}s (${correctPercentage.toFixed(1)}%)</div>
                        <div><b>Incorrect posture:</b> ${incorrectTime.toFixed(1)}s (${incorrectPercentage.toFixed(1)}%)</div>
                        <div><b>Total analyzed time:</b> ${(correctTime + incorrectTime).toFixed(1)}s</div>
                    </div>
                    ${improvementText}
                    <div style="margin-top: 15px;">
                        <h3 style="margin: 5px 0;">Presentation Tips</h3>
                        <ul style="margin: 5px 0; padding-left: 20px;">
                            <li>Maintain eye contact with your audience</li>
                            <li>Use open hand gestures to emphasize points</li>
                            <li>Distribute weight evenly on both feet</li>
                            <li>Keep shoulders relaxed and back straight</li>
                        </ul>
                    </div>
                `;
                
                // Update progress tracking data
                progressData.sessionsCompleted += 1;
                progressData.totalPracticeTime += (correctTime + incorrectTime) / 60; // Convert seconds to minutes
                
                // Save updated progress data
                localStorage.setItem('presentationProgressData', JSON.stringify(progressData));
                
                // Update progress display
                updateProgressDisplay();
                
                // Reset counters for next 5 min interval
                correctFrames = 0; incorrectFrames = 0; totalFrames = 0;
            }

            main();
        </script>
    </body>
</html>
"""
