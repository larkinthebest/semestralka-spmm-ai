// static/quiz.js

import { showNotification, showLoadingMessage, removeLoadingMessage } from "./ui.js";
import { generateQuizApi, submitQuizApi, fetchQuizStatsApi } from "./api.js";
import { currentChatId, currentMode, currentTutor, chatModeHistory, currentLanguage, translations, setCurrentChatId, setCurrentMode, setCurrentTutor, setChatModeHistory, updateChatModeHistory, addMessageToChatModeHistory, deleteChatHistory, setCurrentLanguage } from "./app.js"; // Import necessary globals from app.js
import { loadProfileQuizHistory } from "./profile.js"; // Import from profile.js

export let currentQuiz = null;
export function setCurrentQuiz(quiz) { currentQuiz = quiz; }

export let quizAnswers = {};
export function setQuizAnswers(answers) { quizAnswers = answers; }
export function updateQuizAnswer(questionIndex, answer) { quizAnswers[questionIndex] = answer; }

export let currentQuestionIndex = 0;
export function setCurrentQuestionIndex(index) { currentQuestionIndex = index; }

export async function generateQuiz(message, allAvailableFiles) {
  const quizNumQuestionsInput = document.getElementById("quizNumQuestions");
  const quizTypeInput = document.getElementById("quizType");
  const quizDifficultyInput = document.getElementById("quizDifficulty");

  const quizType = quizTypeInput ? quizTypeInput.value : "multiple_choice";
  const numQuestions = quizNumQuestionsInput ? parseInt(quizNumQuestionsInput.value) : 5;
  const quizDifficulty = quizDifficultyInput ? quizDifficultyInput.value : "";
  const quizTopic = message.trim();

  if (numQuestions < 1 || numQuestions > 20) {
    showNotification(
      "Please specify a number of questions between 1 and 20.",
      "warning"
    );
    return;
  }

  if (allAvailableFiles.length === 0) {
    showNotification(
      "Please upload files first to generate a quiz!",
      "warning"
    );
    return;
  }

  showLoadingMessage(currentTutor);

  try {
    const data = await generateQuizApi({
      topic: quizTopic,
      quiz_type: quizType,
      num_questions: numQuestions,
      difficulty: quizDifficulty,
      attached_files: allAvailableFiles,
      language: currentLanguage,
    });

    removeLoadingMessage();

    displayQuiz(data);
    const chatKey = `${currentChatId}_${currentMode}`;
    addMessageToChatModeHistory(chatKey, {
      type: "bot",
      content: `Generated a ${quizType} quiz with ${numQuestions} questions on ${
        quizTopic || "general topics"
      } (Difficulty: ${quizDifficulty || "any"}).`,
      quizData: data,
    });
    localStorage.setItem(
      "chatModeHistory",
      JSON.stringify(chatModeHistory)
    );
    // saveChatToDatabase is called from chat.js after sendMessage
    return data; // Return the quiz data so sendMessage can use suggested_title
  } catch (error) {
    console.error("Error generating quiz:", error);
    removeLoadingMessage();
    showNotification(error.message || "Failed to generate quiz.", "error");
    throw error; // Re-throw the error so sendMessage can handle it
  }
}

export function displayQuiz(quizData) {
  const quizPanel = document.getElementById("quizPanel");
  const quizContainer = document.getElementById("quizContainer");
  const sourcePanel = document.querySelector(".source-panel");

  if (!quizPanel || !quizContainer || !sourcePanel) {
    console.error("Quiz UI elements not found!");
    return;
  }

  setCurrentQuiz(quizData);
  setQuizAnswers({});
  setCurrentQuestionIndex(0);

  quizPanel.style.display = "block";
  sourcePanel.style.display = "none";

  let quizHtml = `
    <div class="quiz-container">
      <div class="quiz-header">
        <div class="quiz-title">${
          quizData.title || "Interactive Quiz"
        }</div>
        <div class="quiz-progress">Question ${currentQuestionIndex + 1} of ${
          quizData.questions ? quizData.questions.length : 0
        }</div>
      </div>
      <div id="quizQuestions">
  `;

  if (quizData.questions && quizData.questions.length > 0) {
    quizData.questions.forEach((question, index) => {
      quizHtml += `
        <div class="quiz-question" id="question-${index}" style="${
        index === currentQuestionIndex ? "" : "display: none;"
      }">
          <div class="question-text">${index + 1}. ${
        question.question_text
      }</div>
      `;

      if (question.question_type === "multiple_choice") {
        quizHtml += '<div class="quiz-options">';
        question.options.forEach((option, optIndex) => {
          const letter = String.fromCharCode(65 + optIndex);
          quizHtml += `
            <div class="quiz-option" data-question-index="${index}" data-answer="${option}" onclick="window.selectQuizOption(${index}, '${option}', this)">
              <span class="option-letter">${letter})</span>
              <span>${option}</span>
            </div>
          `;
        });
        quizHtml += "</div>";
      } else if (question.question_type === "true_false") {
        quizHtml += `
          <div class="quiz-options">
            <div class="quiz-option" data-question-index="${index}" data-answer="True" onclick="window.selectQuizOption(${index}, 'True', this)">
              <span>True</span>
            </div>
            <div class="quiz-option" data-question-index="${index}" data-answer="False" onclick="window.selectQuizOption(${index}, 'False', this)">
              <span>False</span>
            </div>
          </div>
        `;
      } else if (question.question_type === "fill_in_the_blank") {
        quizHtml += `
          <input type="text" class="quiz-input" placeholder="Type your answer here..." 
                 onchange="window.updateQuizAnswer(${index}, this.value)" value="${quizAnswers[index] || ''}">
        `;
      } else if (question.question_type === "short_answer") {
        quizHtml += `
          <textarea class="quiz-input" placeholder="Write your answer in 2-3 sentences..." 
                   onchange="window.updateQuizAnswer(${index}, this.value)" rows="3">${quizAnswers[index] || ''}</textarea>
        `;
      }

      quizHtml += "</div>";
    });
  } else {
    quizHtml += `
      <div class="quiz-question">
        <div class="question-text">No questions were generated for this quiz. Please try again with different settings or content.</div>
      </div>
    `;
  }

  quizHtml += `
      </div>
      <div class="quiz-actions">
        <button class="quiz-btn secondary" onclick="window.previousQuestion()" id="prevBtn" style="display: none;">Previous</button>
        <button class="quiz-btn primary" onclick="window.nextQuestion()" id="nextBtn">Next</button>
        <button class="quiz-btn primary" onclick="window.submitQuiz()" id="submitBtn" style="display: none;">Submit Quiz</button>
      </div>
    </div>
  `;

  quizContainer.innerHTML = quizHtml;

  for (const qIndex in quizAnswers) {
    const questionType = quizData.questions[qIndex].question_type;
    if (questionType === "multiple_choice" || questionType === "true_false") {
      const selectedOptionElement = quizContainer.querySelector(
        `.quiz-option[data-question-index="${qIndex}"][data-answer="${quizAnswers[qIndex]}"]`
      );
      if (selectedOptionElement) {
        selectedOptionElement.classList.add("selected");
      }
    }
  }

  updateQuizNavigationButtons();
}

export function updateQuizNavigationButtons() {
  const questions = document.querySelectorAll(".quiz-question");
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");
  const submitBtn = document.getElementById("submitBtn");
  const quizProgress = document.querySelector(".quiz-progress");

  if (questions.length === 0) {
    if (prevBtn) prevBtn.style.display = "none";
    if (nextBtn) nextBtn.style.display = "none";
    if (submitBtn) submitBtn.style.display = "none";
    if (quizProgress) quizProgress.textContent = "No questions";
    return;
  }

  if (prevBtn) prevBtn.style.display = currentQuestionIndex > 0 ? "inline-block" : "none";
  if (nextBtn) nextBtn.style.display = currentQuestionIndex < questions.length - 1 ? "inline-block" : "none";
  if (submitBtn) submitBtn.style.display = currentQuestionIndex === questions.length - 1 ? "inline-block" : "none";
  if (quizProgress) quizProgress.textContent = `Question ${currentQuestionIndex + 1} of ${questions.length}`;
}

export function selectQuizOption(questionIndex, answer, element) {
  element.parentNode.querySelectorAll(".quiz-option").forEach((opt) => {
    opt.classList.remove("selected");
  });
  element.classList.add("selected");
  updateQuizAnswer(questionIndex, answer);
}

export function nextQuestion() {
  const questions = document.querySelectorAll(".quiz-question");
  if (currentQuestionIndex < questions.length - 1) {
    questions[currentQuestionIndex].style.display = "none";
    setCurrentQuestionIndex(currentQuestionIndex + 1);
    questions[currentQuestionIndex].style.display = "block";

    const quizProgress = document.querySelector(".quiz-progress");
    if (quizProgress) quizProgress.textContent = `Question ${
      currentQuestionIndex + 1
    } of ${questions.length}`;

    const prevBtn = document.getElementById("prevBtn");
    if (prevBtn) prevBtn.style.display = "inline-block";

    if (currentQuestionIndex === questions.length - 1) {
      const nextBtn = document.getElementById("nextBtn");
      if (nextBtn) nextBtn.style.display = "none";
      const submitBtn = document.getElementById("submitBtn");
      if (submitBtn) submitBtn.style.display = "inline-block";
    }
  }
}

export function previousQuestion() {
  const questions = document.querySelectorAll(".quiz-question");
  if (currentQuestionIndex > 0) {
    questions[currentQuestionIndex].style.display = "none";
    setCurrentQuestionIndex(currentQuestionIndex - 1);
    questions[currentQuestionIndex].style.display = "block";

    const quizProgress = document.querySelector(".quiz-progress");
    if (quizProgress) quizProgress.textContent = `Question ${
      currentQuestionIndex + 1
    } of ${questions.length}`;

    if (currentQuestionIndex === 0) {
      const prevBtn = document.getElementById("prevBtn");
      if (prevBtn) prevBtn.style.display = "none";
    }

    const nextBtn = document.getElementById("nextBtn");
    if (nextBtn) nextBtn.style.display = "inline-block";
    const submitBtn = document.getElementById("submitBtn");
    if (submitBtn) submitBtn.style.display = "none";
  }
}

export async function submitQuiz() {
  if (!currentQuiz) return;

  const accessToken = localStorage.getItem("access_token");
  if (!accessToken) {
    showNotification("Please sign in to submit quizzes.", "error");
    return;
  }

  const submitBtn = document.getElementById("submitBtn");
  if (submitBtn) submitBtn.disabled = true;
  const nextBtn = document.getElementById("nextBtn");
  if (nextBtn) nextBtn.disabled = true;
  const prevBtn = document.getElementById("prevBtn");
  if (prevBtn) prevBtn.disabled = true;

  const userAnswersForSubmission = [];

  currentQuiz.questions.forEach((question, index) => {
    const userAnswer = quizAnswers[index];
    userAnswersForSubmission.push({
      question_id: question.id,
      user_answer: userAnswer || "",
    });
  });

  showLoadingMessage(currentTutor);

  try {
    const data = await submitQuizApi({
      quiz_id: currentQuiz.id,
      answers: userAnswersForSubmission,
    });

    removeLoadingMessage();
    showNotification("Quiz submitted successfully!", "success");

    // After submission, refresh quiz history in profile
    await loadProfileQuizHistory();

    // Re-enable buttons
    if (submitBtn) submitBtn.disabled = false;
    if (nextBtn) nextBtn.disabled = false;
    if (prevBtn) prevBtn.disabled = false;

    // Display results in chat
    displayQuizResultsInChat(data);

    // Hide quiz panel after displaying results
    hideQuiz();

  } catch (error) {
    console.error("Error submitting quiz:", error);
    removeLoadingMessage();
    showNotification(error.message || "Error submitting the quiz.", "error");

    // Re-enable buttons on error
    if (submitBtn) submitBtn.disabled = false;
    if (nextBtn) nextBtn.disabled = false;
    if (prevBtn) prevBtn.disabled = false;
  }
}

export function hideQuiz() {
  const quizPanel = document.getElementById("quizPanel");
  if (quizPanel) quizPanel.style.display = "none";
  const sourcePanel = document.querySelector(".source-panel");
  if (sourcePanel) sourcePanel.style.display = "block";
  setCurrentQuiz(null);
  setQuizAnswers({});
  setCurrentQuestionIndex(0);
}

export function applyQuizSettings() {
  showNotification("Quiz settings applied!", "info");
}

import { addMessage } from "./ui.js"; // Import addMessage

export function displayQuizResultsInChat(quizResult) {
  const { quiz_title, score, total_questions, percentage, questions, study_suggestions } = quizResult;

  let resultHtml = `
    <h3>📝 Quiz Results: ${quiz_title || 'Untitled Quiz'}</h3>
    <p><strong>Score:</strong> ${score}/${total_questions} (${percentage}%)</p>
    <br>
  `;

  if (questions && questions.length > 0) {
    questions.forEach((q, index) => {
      resultHtml += `
        <div style="margin-bottom: 10px; padding: 8px; border-left: 4px solid ${q.is_correct ? '#4caf50' : '#f44336'}; background-color: var(--bg-tertiary); border-radius: 4px;">
          <p><strong>Question ${index + 1}:</strong> ${q.question_text}</p>
          <p><strong>Your Answer:</strong> ${q.user_answer || 'N/A'}</p>
          <p><strong>Correct Answer:</strong> ${q.correct_answer || 'N/A'}</p>
          <p style="color: ${q.is_correct ? '#4caf50' : '#f44336'};"><strong>Status:</strong> ${q.is_correct ? 'Correct' : 'Incorrect'}</p>
          ${q.explanation ? `<p><strong>Explanation:</strong> ${q.explanation}</p>` : ''}
        </div>
      `;
    });
  } else {
    resultHtml += `<p>No question details available for this quiz result.</p>`;
  }


  if (study_suggestions && study_suggestions.length > 0) {
    resultHtml += `
      <br>
      <h4>💡 Study Suggestions:</h4>
      <ul>
        ${study_suggestions.map(s => `<li>${s}</li>`).join('')}
      </ul>
    `;
  } else {
    resultHtml += `<p>No study suggestions available.</p>`;
  }

  addMessage(resultHtml, "bot", currentTutor);
  const chatKey = `${currentChatId}_${currentMode}`;
  addMessageToChatModeHistory(chatKey, {
    type: "bot",
    content: resultHtml,
    quizResultData: quizResult, // Store full result for potential re-display
  });
  localStorage.setItem("chatModeHistory", JSON.stringify(chatModeHistory));
}
