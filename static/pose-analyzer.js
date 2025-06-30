/**
 * Pose Analyzer for Presentation Practice
 * This module handles body language detection and analysis for presentations
 */

class PoseAnalyzer {
    constructor() {
        // Landmark indices for reference
        this.NOSE = 0;
        this.LEFT_SHOULDER = 11;
        this.RIGHT_SHOULDER = 12;
        this.LEFT_ELBOW = 13;
        this.RIGHT_ELBOW = 14;
        this.LEFT_WRIST = 15;
        this.RIGHT_WRIST = 16;
        this.LEFT_HIP = 23;
        this.RIGHT_HIP = 24;
        this.LEFT_KNEE = 25;
        this.RIGHT_KNEE = 26;
        this.LEFT_ANKLE = 27;
        this.RIGHT_ANKLE = 28;
    }

    /**
     * Analyzes body language for presentation posture
     * @param {Array} landmarks - The pose landmarks from MediaPipe
     * @returns {Object} Analysis result with isCorrect flag and feedback
     */
    analyzePresentationPosture(landmarks) {
        // Check if key landmarks are detected
        if (!this._areKeyLandmarksVisible(landmarks)) {
            return { isCorrect: false, feedback: "Move fully into camera view" };
        }
        
        // Extract key landmarks
        const nose = landmarks[this.NOSE];
        const leftShoulder = landmarks[this.LEFT_SHOULDER];
        const rightShoulder = landmarks[this.RIGHT_SHOULDER];
        const leftElbow = landmarks[this.LEFT_ELBOW];
        const rightElbow = landmarks[this.RIGHT_ELBOW];
        const leftWrist = landmarks[this.LEFT_WRIST];
        const rightWrist = landmarks[this.RIGHT_WRIST];
        const leftHip = landmarks[this.LEFT_HIP];
        const rightHip = landmarks[this.RIGHT_HIP];
        const leftKnee = landmarks[this.LEFT_KNEE];
        const rightKnee = landmarks[this.RIGHT_KNEE];
        const leftAnkle = landmarks[this.LEFT_ANKLE];
        const rightAnkle = landmarks[this.RIGHT_ANKLE];
        
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
            feedback: isCorrect ? "Great presentation posture!" : feedbackItems.join(" & "),
            details: {
                shouldersAligned,
                hipsAligned,
                backStraight,
                headCentered,
                headUpright,
                armsNotCrossed,
                armsInGesturingPosition,
                weightBalanced,
                shouldersRelaxed
            }
        };
    }

    /**
     * Highlights problematic areas on the canvas
     * @param {CanvasRenderingContext2D} ctx - Canvas context
     * @param {Array} landmarks - The pose landmarks
     * @param {Object} analysisResult - Result from analyzePresentationPosture
     * @param {number} canvasWidth - Width of the canvas
     * @param {number} canvasHeight - Height of the canvas
     */
    drawFeedbackVisualization(ctx, landmarks, analysisResult, canvasWidth, canvasHeight) {
        if (!analysisResult.isCorrect) {
            const feedback = analysisResult.feedback;
            const details = analysisResult.details;
            
            // Highlight problematic areas with colored circles
            if (!details.shouldersAligned || !details.shouldersRelaxed) {
                this._highlightLandmarks(ctx, [landmarks[this.LEFT_SHOULDER], landmarks[this.RIGHT_SHOULDER]], 
                                       'yellow', canvasWidth, canvasHeight);
            }
            
            if (!details.backStraight) {
                // Draw line from shoulders to hips to show alignment
                const shoulderMidX = (landmarks[this.LEFT_SHOULDER].x + landmarks[this.RIGHT_SHOULDER].x) / 2;
                const shoulderMidY = (landmarks[this.LEFT_SHOULDER].y + landmarks[this.RIGHT_SHOULDER].y) / 2;
                const hipMidX = (landmarks[this.LEFT_HIP].x + landmarks[this.RIGHT_HIP].x) / 2;
                const hipMidY = (landmarks[this.LEFT_HIP].y + landmarks[this.RIGHT_HIP].y) / 2;
                
                ctx.beginPath();
                ctx.moveTo(shoulderMidX * canvasWidth, shoulderMidY * canvasHeight);
                ctx.lineTo(hipMidX * canvasWidth, hipMidY * canvasHeight);
                ctx.strokeStyle = 'yellow';
                ctx.lineWidth = 3;
                ctx.stroke();
            }
            
            if (!details.armsNotCrossed || !details.armsInGesturingPosition) {
                this._highlightLandmarks(ctx, 
                    [landmarks[this.LEFT_ELBOW], landmarks[this.RIGHT_ELBOW], 
                     landmarks[this.LEFT_WRIST], landmarks[this.RIGHT_WRIST]], 
                    'orange', canvasWidth, canvasHeight);
            }
            
            if (!details.headCentered || !details.headUpright) {
                this._highlightLandmarks(ctx, [landmarks[this.NOSE]], 'cyan', canvasWidth, canvasHeight);
            }
            
            if (!details.weightBalanced || !details.hipsAligned) {
                this._highlightLandmarks(ctx, 
                    [landmarks[this.LEFT_ANKLE], landmarks[this.RIGHT_ANKLE]], 
                    'magenta', canvasWidth, canvasHeight);
            }
        }
    }

    /**
     * Checks if all required landmarks are visible
     * @private
     * @param {Array} landmarks - The pose landmarks
     * @returns {boolean} True if all key landmarks are visible
     */
    _areKeyLandmarksVisible(landmarks) {
        const requiredLandmarks = [
            this.NOSE, this.LEFT_SHOULDER, this.RIGHT_SHOULDER, 
            this.LEFT_ELBOW, this.RIGHT_ELBOW, this.LEFT_WRIST, 
            this.RIGHT_WRIST, this.LEFT_HIP, this.RIGHT_HIP,
            this.LEFT_ANKLE, this.RIGHT_ANKLE
        ];
        
        return requiredLandmarks.every(index => landmarks[index]);
    }

    /**
     * Helper function to highlight specific landmarks
     * @private
     * @param {CanvasRenderingContext2D} ctx - Canvas context
     * @param {Array} landmarkArray - Array of landmarks to highlight
     * @param {string} color - Color to use for highlighting
     * @param {number} canvasWidth - Width of the canvas
     * @param {number} canvasHeight - Height of the canvas
     */
    _highlightLandmarks(ctx, landmarkArray, color, canvasWidth, canvasHeight) {
        landmarkArray.forEach(landmark => {
            if (landmark) {
                ctx.beginPath();
                ctx.arc(landmark.x * canvasWidth, landmark.y * canvasHeight, 15, 0, 2 * Math.PI);
                ctx.strokeStyle = color;
                ctx.lineWidth = 3;
                ctx.stroke();
            }
        });
    }
}

// Export the class for use in other files
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = PoseAnalyzer;
} else {
    window.PoseAnalyzer = PoseAnalyzer;
}