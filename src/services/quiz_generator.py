from typing import List, Dict, Any
import random
import re

class QuizGenerator:
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.quiz_types = ["multiple_choice", "true_false", "fill_blank"]
    
    async def generate_quiz(self, content: str, quiz_type: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """Generate quiz questions from content"""
        if quiz_type not in self.quiz_types:
            raise ValueError(f"Unsupported quiz type: {quiz_type}")
        
        # Clean and prepare content
        cleaned_content = self._prepare_content(content)
        
        # Generate questions using LLM
        questions = await self.llm_service.generate_quiz_questions(
            cleaned_content, quiz_type, num_questions
        )
        
        # Validate and format questions
        formatted_questions = []
        for i, question in enumerate(questions):
            formatted_question = self._format_question(question, quiz_type, i + 1)
            if formatted_question:
                formatted_questions.append(formatted_question)
        
        return formatted_questions[:num_questions]
    
    def _prepare_content(self, content: str) -> str:
        """Clean and prepare content for quiz generation"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Limit content length to avoid token limits
        if len(content) > 2000:
            # Try to break at sentence boundaries
            sentences = content.split('.')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence) < 2000:
                    truncated += sentence + "."
                else:
                    break
            content = truncated
        
        return content.strip()
    
    def _format_question(self, question_data: Dict, quiz_type: str, question_num: int) -> Dict[str, Any]:
        """Format question data into standardized structure"""
        if not question_data.get("question"):
            return None
        
        formatted = {
            "id": question_num,
            "question": question_data["question"],
            "type": quiz_type
        }
        
        if quiz_type == "multiple_choice":
            options = question_data.get("options", [])
            if len(options) < 2:
                # Generate default options if not provided
                options = self._generate_default_options(question_data["question"])
            
            formatted["options"] = options
            formatted["correct_answer"] = question_data.get("correct_answer", "A")
            
        elif quiz_type == "true_false":
            formatted["options"] = ["True", "False"]
            correct = question_data.get("correct_answer", "True")
            formatted["correct_answer"] = correct if correct in ["True", "False"] else "True"
            
        elif quiz_type == "fill_blank":
            formatted["correct_answer"] = question_data.get("correct_answer", "answer")
            # Ensure question has a blank
            if "_____" not in formatted["question"]:
                formatted["question"] += " _____"
        
        # Add explanation if available
        if question_data.get("explanation"):
            formatted["explanation"] = question_data["explanation"]
        
        return formatted
    
    def _generate_default_options(self, question: str) -> List[str]:
        """Generate default multiple choice options"""
        # This is a fallback - in practice, the LLM should provide options
        return [
            "Option A",
            "Option B", 
            "Option C",
            "Option D"
        ]
    
    def validate_quiz(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate quiz questions and return validation results"""
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "question_count": len(questions)
        }
        
        for i, question in enumerate(questions):
            question_num = i + 1
            
            # Check required fields
            if not question.get("question"):
                results["errors"].append(f"Question {question_num}: Missing question text")
                results["valid"] = False
            
            if not question.get("correct_answer"):
                results["errors"].append(f"Question {question_num}: Missing correct answer")
                results["valid"] = False
            
            # Type-specific validation
            quiz_type = question.get("type")
            
            if quiz_type == "multiple_choice":
                options = question.get("options", [])
                if len(options) < 2:
                    results["errors"].append(f"Question {question_num}: Need at least 2 options")
                    results["valid"] = False
                
                correct_answer = question.get("correct_answer")
                if correct_answer not in ["A", "B", "C", "D"] and len(options) > 0:
                    results["warnings"].append(f"Question {question_num}: Unusual correct answer format")
            
            elif quiz_type == "true_false":
                correct_answer = question.get("correct_answer")
                if correct_answer not in ["True", "False"]:
                    results["errors"].append(f"Question {question_num}: True/False answer must be 'True' or 'False'")
                    results["valid"] = False
            
            elif quiz_type == "fill_blank":
                if "_____" not in question.get("question", ""):
                    results["warnings"].append(f"Question {question_num}: No blank found in fill-in-the-blank question")
        
        return results
    
    def get_quiz_statistics(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the quiz"""
        if not questions:
            return {"total_questions": 0}
        
        type_counts = {}
        for question in questions:
            quiz_type = question.get("type", "unknown")
            type_counts[quiz_type] = type_counts.get(quiz_type, 0) + 1
        
        return {
            "total_questions": len(questions),
            "types": type_counts,
            "has_explanations": sum(1 for q in questions if q.get("explanation")),
            "average_question_length": sum(len(q.get("question", "")) for q in questions) / len(questions)
        }