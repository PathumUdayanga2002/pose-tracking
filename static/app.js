/**
 * Presentation Practice Application
 * Main application logic for body language tracking during presentations
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const videoElement = document.querySelector('.input_video');
    const canvasElement = document.querySelector('.output_canvas');
    const canvasCtx = canvasElement.getContext('2d');
    const feedbackDiv = document.getElementById('feedback');
    const chartContainer = document.getElementById('chart-container');
    const statsDiv = document.getElementById('stats');
    const sessionStatsDiv = document.getElementById('session-stats');
    const sessionsCountElement = document.getElementById('sessions-count');
    const totalPracticeTimeElement = document.getElementById('total-practice-time');
    
    // Initialize pose analyzer
    const poseAnalyzer = new PoseAnalyzer();
    
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
    
    // Session history for tracking improvement
    let sessionHistory = [];
    
    // Initialize the application
    function init() {
        // Try to load existing progress data
        loadProgressData();
        
        // Initialize MediaPipe Pose
        initializePose();
        
        // Initialize camera
        initializeCamera();
        
        // Initialize chart
        initializeChart();
        
        // Show UI elements
        chartContainer.style.display = 'block';
        statsDiv.style.display = 'block';
    }
    
    // Load progress data from localStorage
    function loadProgressData() {
        try {
            // Load progress data
            const savedProgressData = localStorage.getItem('presentationProgressData');
            if (savedProgressData) {
                progressData = JSON.parse(savedProgressData);
            }
            
            // Load session history
            const savedSessionHistory = localStorage.getItem('presentationSessionHistory');
            if (savedSessionHistory) {
                sessionHistory = JSON.parse(savedSessionHistory);
            }
            
            // Update UI with loaded data
            updateProgressDisplay();
        } catch (e) {
            console.error('Error loading progress data:', e);
        }
    }
    
    // Update progress display
    function updateProgressDisplay() {
        sessionsCountElement.textContent = progressData.sessionsCompleted;
        totalPracticeTimeElement.textContent = progressData.totalPracticeTime.toFixed(1);
    }
    
    // Initialize MediaPipe Pose
    function initializePose() {
        const pose = new window.Pose({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`,
        });
        
        pose.setOptions({
            modelComplexity: 1,
            smoothLandmarks: true,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });
        
        pose.onResults(onResults);
        
        // Start detection loop
        const processVideo = async () => {
            if (videoElement.readyState >= 2) {
                await pose.send({ image: videoElement });
            }
            requestAnimationFrame(processVideo);
        };
        
        processVideo();
    }
    
    // Initialize camera
    function initializeCamera() {
        navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
            .then(stream => {
                videoElement.srcObject = stream;
            })
            .catch(err => {
                console.error("Error accessing webcam: ", err);
                feedbackDiv.textContent = "Error: Cannot access camera";
                feedbackDiv.style.color = "red";
            });
    }
    
    // Initialize chart
    function initializeChart() {
        const chartCtx = document.getElementById('postureChart').getContext('2d');
        pieChart = new Chart(chartCtx, {
            type: 'pie',
            data: {
                labels: ['Correct Posture', 'Incorrect Posture'],
                datasets: [{
                    data: [50, 50], // Initial placeholder data
                    backgroundColor: ['rgba(75, 192, 192, 0.8)', 'rgba(255, 99, 132, 0.8)'],
                    borderColor: ['rgba(75, 192, 192, 1)', 'rgba(255, 99, 132, 1)'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'bottom' },
                    title: { display: true, text: 'Body Language Analysis' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.raw.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Process pose detection results
    function onResults(results) {
        // Clear canvas and draw video frame
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
        canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);
        
        if (results.poseLandmarks) {
            // Draw pose landmarks
            window.drawConnectors(canvasCtx, results.poseLandmarks, window.POSE_CONNECTIONS, 
                                 {color: '#00FF00', lineWidth: 4});
            window.drawLandmarks(canvasCtx, results.poseLandmarks, 
                               {color: '#FF0000', lineWidth: 2});
            
            // Analyze body language
            const analysisResult = poseAnalyzer.analyzePresentationPosture(results.poseLandmarks);
            
            // Update counters
            if (analysisResult.isCorrect) {
                feedbackDiv.style.color = 'green';
                correctFrames++;
            } else {
                feedbackDiv.style.color = 'red';
                incorrectFrames++;
            }
            
            // Display feedback
            feedbackDiv.textContent = analysisResult.feedback;
            totalFrames++;
            
            // Draw feedback visualizations
            poseAnalyzer.drawFeedbackVisualization(
                canvasCtx, 
                results.poseLandmarks, 
                analysisResult, 
                canvasElement.width, 
                canvasElement.height
            );
            
            // Update chart periodically
            updateChart();
            
            // Every 5 minutes (300000 ms), show detailed stats
            const now = Date.now();
            if (now - lastChartTime > 300000 && totalFrames > 0) {
                saveSessionData();
                lastChartTime = now;
            }
        } else {
            feedbackDiv.textContent = 'No pose detected';
        }
    }
    
    // Update chart with current data
    function updateChart() {
        if (totalFrames > 0 && pieChart) {
            const correctPercentage = (correctFrames / totalFrames) * 100;
            const incorrectPercentage = (incorrectFrames / totalFrames) * 100;
            
            pieChart.data.datasets[0].data[0] = correctPercentage;
            pieChart.data.datasets[0].data[1] = incorrectPercentage;
            pieChart.update();
            
            // Update session stats
            correctTime = correctFrames * (1/30); // assuming ~30 FPS
            incorrectTime = incorrectFrames * (1/30);
            
            sessionStatsDiv.innerHTML = `
                <div>
                    <p><b>Correct posture:</b> ${correctTime.toFixed(1)}s (${correctPercentage.toFixed(1)}%)</p>
                    <p><b>Incorrect posture:</b> ${incorrectTime.toFixed(1)}s (${incorrectPercentage.toFixed(1)}%)</p>
                    <p><b>Total analyzed time:</b> ${(correctTime + incorrectTime).toFixed(1)}s</p>
                </div>
            `;
        }
    }
    
    // Save session data after 5 minutes
    function saveSessionData() {
        // Calculate time in seconds
        correctTime = correctFrames * (1/30);
        incorrectTime = incorrectFrames * (1/30);
        
        // Store session data for tracking improvement
        const sessionData = {
            timestamp: Date.now(),
            correctPercentage: (correctFrames / totalFrames) * 100,
            correctTime: correctTime,
            incorrectTime: incorrectTime,
            totalTime: correctTime + incorrectTime
        };
        sessionHistory.push(sessionData);
        
        // Save session history to localStorage
        localStorage.setItem('presentationSessionHistory', JSON.stringify(sessionHistory));
        
        // Calculate improvement metrics
        let improvementText = '';
        if (sessionHistory.length > 1) {
            const currentSession = sessionHistory[sessionHistory.length - 1];
            const previousSession = sessionHistory[sessionHistory.length - 2];
            
            const percentageChange = currentSession.correctPercentage - previousSession.correctPercentage;
            const improvementDirection = percentageChange >= 0 ? 'improved' : 'decreased';
            const cssClass = percentageChange >= 0 ? 'improvement-positive' : 'improvement-negative';
            
            improvementText = `
                <div class="${cssClass}">
                    <b>Improvement:</b> Your correct posture has ${improvementDirection} by 
                    ${Math.abs(percentageChange).toFixed(1)}% since last session
                </div>
            `;
        }
        
        // Update session stats with improvement info
        sessionStatsDiv.innerHTML += improvementText;
        
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
    
    // Initialize the application
    init();
});