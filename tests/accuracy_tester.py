"""
Transcription Accuracy Testing Module (Task 5)
Tests Whisper transcription accuracy using Word Error Rate (WER) calculation.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transcriber import Transcriber
from src.audio_processor import AudioProcessor


class AccuracyTester:
    """Tests transcription accuracy using Word Error Rate (WER)."""
    
    def __init__(self):
        """Initialize AccuracyTester."""
        self.transcriber = Transcriber(model_size="base")
        self.audio_processor = AudioProcessor(use_temp=True)
    
    def calculate_wer(self, reference: str, hypothesis: str) -> Dict:
        """
        Calculate Word Error Rate (WER) between reference and hypothesis.
        
        WER = (Substitutions + Deletions + Insertions) / Total Reference Words
        
        Args:
            reference: Reference transcript (ground truth)
            hypothesis: Hypothesis transcript (Whisper output)
            
        Returns:
            Dictionary with WER metrics and error details
        """
        # Normalize text
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        # Initialize DP matrix for Levenshtein distance
        m, n = len(ref_words), len(hyp_words)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Initialize first row and column
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        # Fill DP matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if ref_words[i - 1] == hyp_words[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(
                        dp[i - 1][j] + 1,      # Deletion
                        dp[i][j - 1] + 1,      # Insertion
                        dp[i - 1][j - 1] + 1   # Substitution
                    )
        
        # Backtrack to find errors
        substitutions = 0
        deletions = 0
        insertions = 0
        i, j = m, n
        
        while i > 0 or j > 0:
            if i > 0 and j > 0 and ref_words[i - 1] == hyp_words[j - 1]:
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
                substitutions += 1
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
                deletions += 1
                i -= 1
            elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
                insertions += 1
                j -= 1
            else:
                i -= 1
                j -= 1
        
        total_errors = substitutions + deletions + insertions
        total_ref_words = len(ref_words)
        
        wer = (total_errors / total_ref_words * 100) if total_ref_words > 0 else 0
        accuracy = 100 - wer
        
        return {
            "wer": wer,
            "accuracy": accuracy,
            "substitutions": substitutions,
            "deletions": deletions,
            "insertions": insertions,
            "total_errors": total_errors,
            "reference_word_count": total_ref_words,
            "hypothesis_word_count": len(hyp_words)
        }
    
    def analyze_errors(self, reference: str, hypothesis: str) -> Dict:
        """
        Analyze specific types of errors in transcription.
        
        Args:
            reference: Reference transcript
            hypothesis: Hypothesis transcript
            
        Returns:
            Dictionary with detailed error analysis
        """
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        # Find missing words
        missing = [w for w in ref_words if w not in hyp_words]
        
        # Find extra words
        extra = [w for w in hyp_words if w not in ref_words]
        
        # Find misrecognized words (similar but not exact)
        misrecognized = []
        for ref_word in ref_words:
            if ref_word not in hyp_words:
                # Check for similar words
                for hyp_word in hyp_words:
                    if self._is_similar_word(ref_word, hyp_word):
                        misrecognized.append({
                            "reference": ref_word,
                            "hypothesis": hyp_word
                        })
                        break
        
        return {
            "missing_words": missing,
            "extra_words": extra,
            "misrecognized_words": misrecognized,
            "missing_count": len(missing),
            "extra_count": len(extra),
            "misrecognized_count": len(misrecognized)
        }
    
    def _is_similar_word(self, word1: str, word2: str) -> bool:
        """
        Check if two words are similar (potential misrecognition).
        
        Args:
            word1: First word
            word2: Second word
            
        Returns:
            True if words are similar
        """
        # Simple similarity check: edit distance <= 2 or length difference <= 1
        if abs(len(word1) - len(word2)) > 2:
            return False
        
        # Check for common prefix/suffix
        if word1[:3] == word2[:3] or word1[-3:] == word2[-3:]:
            return True
        
        return False
    
    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file using Whisper.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        result = self.transcriber.transcribe(audio_path)
        return result["text"]
    
    def run_test(self, audio_path: str, reference_transcript: str, test_name: str) -> Dict:
        """
        Run accuracy test on a single audio file.
        
        Args:
            audio_path: Path to audio file
            reference_transcript: Reference transcript (ground truth)
            test_name: Name of the test
            
        Returns:
            Dictionary with test results
        """
        print(f"\n🧪 Running test: {test_name}")
        print(f"📁 Audio file: {audio_path}")
        
        # Transcribe audio
        hypothesis = self.transcribe_audio(audio_path)
        
        # Calculate WER
        wer_metrics = self.calculate_wer(reference_transcript, hypothesis)
        
        # Analyze errors
        error_analysis = self.analyze_errors(reference_transcript, hypothesis)
        
        # Compile results
        results = {
            "test_name": test_name,
            "audio_path": audio_path,
            "reference_transcript": reference_transcript,
            "hypothesis_transcript": hypothesis,
            "wer_metrics": wer_metrics,
            "error_analysis": error_analysis,
            "meets_target": wer_metrics["accuracy"] >= 90.0
        }
        
        return results
    
    def generate_report(self, test_results: List[Dict], output_path: str) -> None:
        """
        Generate comprehensive test report.
        
        Args:
            test_results: List of test result dictionaries
            output_path: Path to save report
        """
        # Calculate overall statistics
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r["meets_target"])
        
        if total_tests > 0:
            avg_accuracy = sum(r["wer_metrics"]["accuracy"] for r in test_results) / total_tests
            avg_wer = sum(r["wer_metrics"]["wer"] for r in test_results) / total_tests
        else:
            avg_accuracy = 0
            avg_wer = 0
        
        # Generate report
        report = {
            "summary": {
                "total_tests": total_tests,
                "tests_passed": passed_tests,
                "tests_failed": total_tests - passed_tests,
                "target_accuracy": 90.0,
                "average_accuracy": avg_accuracy,
                "average_wer": avg_wer,
                "target_met": avg_accuracy >= 90.0
            },
            "test_results": test_results,
            "recommendations": self._generate_recommendations(test_results, avg_accuracy)
        }
        
        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Report saved to: {output_path}")
    
    def _generate_recommendations(self, test_results: List[Dict], avg_accuracy: float) -> List[str]:
        """
        Generate recommendations based on test results.
        
        Args:
            test_results: List of test results
            avg_accuracy: Average accuracy across tests
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if avg_accuracy < 90.0:
            recommendations.append("⚠️ Overall accuracy is below the 90% target.")
            
            # Analyze common error patterns
            total_missing = sum(r["error_analysis"]["missing_count"] for r in test_results)
            total_extra = sum(r["error_analysis"]["extra_count"] for r in test_results)
            total_misrecognized = sum(r["error_analysis"]["misrecognized_count"] for r in test_results)
            
            if total_missing > total_extra and total_missing > total_misrecognized:
                recommendations.append("🔍 High deletion rate detected. Consider:")
                recommendations.append("   - Improving audio quality (reduce background noise)")
                recommendations.append("   - Using audio preprocessing (noise reduction, normalization)")
                recommendations.append("   - Ensuring clear speech in recordings")
            
            if total_extra > total_missing and total_extra > total_misrecognized:
                recommendations.append("🔍 High insertion rate detected. Consider:")
                recommendations.append("   - Reducing background noise")
                recommendations.append("   - Using a different Whisper model size")
                recommendations.append("   - Adjusting language settings")
            
            if total_misrecognized > 0:
                recommendations.append("🔍 Word misrecognition detected. Consider:")
                recommendations.append("   - Using a larger Whisper model (medium or large)")
                recommendations.append("   - Providing context-specific vocabulary")
                recommendations.append("   - Fine-tuning the model for specific domain")
            
            recommendations.append("💡 General improvements:")
            recommendations.append("   - Use higher quality audio recordings")
            recommendations.append("   - Ensure proper microphone placement")
            recommendations.append("   - Minimize background noise during recording")
            recommendations.append("   - Consider using the 'medium' or 'large' Whisper model for better accuracy")
        else:
            recommendations.append("✅ Accuracy meets or exceeds the 90% target.")
            recommendations.append("🎉 The Whisper transcription system is performing well.")
        
        return recommendations
    
    def cleanup(self):
        """Clean up temporary files."""
        self.audio_processor.cleanup_temp_files()


def main():
    """Main function to run accuracy tests."""
    tester = AccuracyTester()
    
    try:
        # Define test cases
        test_cases = []
        
        # Check if test dataset exists
        test_data_dir = Path(__file__).parent.parent / "test_data"
        if test_data_dir.exists():
            # Load test cases from test_data directory
            test_config_file = test_data_dir / "test_config.json"
            if test_config_file.exists():
                with open(test_config_file, 'r', encoding='utf-8') as f:
                    test_cases = json.load(f)
            else:
                print("⚠️ No test_config.json found in test_data directory")
                print("📝 Creating sample test configuration...")
                test_cases = []
        else:
            print("⚠️ No test_data directory found")
            print("📝 Please create test_data directory with audio files and reference transcripts")
            print("📝 See README_TESTING.md for instructions")
        
        # Run tests
        results = []
        for test_case in test_cases:
            audio_path = test_case.get("audio_path")
            reference_transcript = test_case.get("reference_transcript")
            test_name = test_case.get("test_name", "Unnamed Test")
            
            if audio_path and reference_transcript:
                try:
                    result = tester.run_test(audio_path, reference_transcript, test_name)
                    results.append(result)
                except Exception as e:
                    print(f"❌ Error running test {test_name}: {e}")
            else:
                print(f"⚠️ Skipping test {test_name}: missing audio_path or reference_transcript")
        
        # Generate report
        if results:
            report_path = Path(__file__).parent.parent / "test_results" / "accuracy_report.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            tester.generate_report(results, str(report_path))
            
            # Print summary
            print("\n" + "="*60)
            print("📊 ACCURACY TEST SUMMARY")
            print("="*60)
            avg_accuracy = sum(r["wer_metrics"]["accuracy"] for r in results) / len(results)
            print(f"Average Accuracy: {avg_accuracy:.2f}%")
            print(f"Target: 90.0%")
            print(f"Status: {'✅ PASSED' if avg_accuracy >= 90.0 else '❌ FAILED'}")
            print("="*60)
        else:
            print("⚠️ No tests were run. Please configure test cases.")
    
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
