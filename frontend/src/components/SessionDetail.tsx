import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useGetSessionQuery, useGetSessionNodesQuery, useAnswerQuestionMutation } from '../services/api';

interface QuestionData {
  question: string;
  options: string[];
  selectionMethod: string;
  allowCustomAnswer: boolean;
  nodeId: string;
}

interface FinalPromptData {
  finalPrompt: string;
  nodeId: string;
}

export default function SessionDetail() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data: session, isLoading: sessionLoading, error: sessionError } = useGetSessionQuery(sessionId!);
  const { data: nodes, isLoading: nodesLoading } = useGetSessionNodesQuery(sessionId!);
  const [answerQuestion, { isLoading: answering }] = useAnswerQuestionMutation();
  
  const [currentQuestion, setCurrentQuestion] = useState<QuestionData | null>(null);
  const [finalPrompt, setFinalPrompt] = useState<FinalPromptData | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<string[]>([]);
  const [customAnswer, setCustomAnswer] = useState('');
  const [isCustomMode, setIsCustomMode] = useState(false);

  if (sessionLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (sessionError || !session) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
        <p className="text-red-600 dark:text-red-400 text-sm">
          Failed to load session. Please try again.
        </p>
      </div>
    );
  }

  const handleAnswerSubmit = async () => {
    if (!currentQuestion) return;

    const answers = isCustomMode && customAnswer.trim() 
      ? [customAnswer.trim()]
      : selectedAnswers;

    if (answers.length === 0) return;

    try {
      const result = await answerQuestion({
        sessionId: sessionId!,
        nodeId: currentQuestion.nodeId,
        selected: answers,
        isCustomAnswer: isCustomMode
      }).unwrap();

      // Reset form state
      setSelectedAnswers([]);
      setCustomAnswer('');
      setIsCustomMode(false);

      // Handle response
      if ('question' in result) {
        setCurrentQuestion(result as QuestionData);
        setFinalPrompt(null);
      } else if ('finalPrompt' in result) {
        setFinalPrompt(result as FinalPromptData);
        setCurrentQuestion(null);
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  const handleCancelSession = async () => {
    if (!currentQuestion) return;

    try {
      await answerQuestion({
        sessionId: sessionId!,
        nodeId: currentQuestion.nodeId,
        selected: [],
        cancel: true
      }).unwrap();

      setCurrentQuestion(null);
    } catch (error) {
      console.error('Failed to cancel session:', error);
    }
  };

  const handleAnswerSelection = (answer: string) => {
    if (!currentQuestion) return;

    if (currentQuestion.selectionMethod === 'single') {
      setSelectedAnswers([answer]);
    } else if (currentQuestion.selectionMethod === 'multi') {
      setSelectedAnswers(prev => 
        prev.includes(answer) 
          ? prev.filter(a => a !== answer)
          : [...prev, answer]
      );
    } else if (currentQuestion.selectionMethod === 'ranking') {
      // For ranking, replace the selection
      setSelectedAnswers([answer]);
    }
  };

  const conversationNodes = nodes ? nodes.filter(node => node.role === 'user' || node.role === 'assistant') : [];

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Session Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          {session.title || 'Untitled Session'}
        </h1>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">Status:</span>
            <span className={`ml-1 capitalize ${
              session.status === 'active' ? 'text-green-600' : 
              session.status === 'completed' ? 'text-blue-600' : 'text-red-600'
            }`}>
              {session.status}
            </span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Model:</span>
            <span className="ml-1 text-gray-900 dark:text-white">{session.target_model}</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Max Questions:</span>
            <span className="ml-1 text-gray-900 dark:text-white">{session.max_questions}</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Created:</span>
            <span className="ml-1 text-gray-900 dark:text-white">
              {new Date(session.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
        
        {session.starter_prompt && (
          <div className="mt-4">
            <span className="text-sm text-gray-500 dark:text-gray-400">Starter Prompt:</span>
            <p className="mt-1 text-gray-900 dark:text-white">{session.starter_prompt}</p>
          </div>
        )}
      </div>

      {/* Conversation History */}
      {conversationNodes.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Conversation</h2>
          <div className="space-y-4">
            {conversationNodes.map((node, index) => (
              <div key={node.id} className={`p-4 rounded-lg ${
                node.role === 'user' 
                  ? 'bg-blue-50 dark:bg-blue-900/20 ml-4' 
                  : 'bg-gray-50 dark:bg-gray-700 mr-4'
              }`}>
                <div className="flex items-center mb-2">
                  <span className={`text-sm font-medium ${
                    node.role === 'user' ? 'text-blue-600' : 'text-gray-600 dark:text-gray-300'
                  }`}>
                    {node.role === 'user' ? 'You' : 'AI'}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                    {new Date(node.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-gray-900 dark:text-white whitespace-pre-wrap">{node.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Current Question */}
      {currentQuestion && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Current Question</h2>
          <p className="text-gray-900 dark:text-white mb-4">{currentQuestion.question}</p>
          
          {!isCustomMode ? (
            <div className="space-y-2 mb-4">
              {currentQuestion.options.map((option, index) => (
                <label key={index} className="flex items-center p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
                  <input
                    type={currentQuestion.selectionMethod === 'single' ? 'radio' : 'checkbox'}
                    name="answer"
                    value={option}
                    checked={selectedAnswers.includes(option)}
                    onChange={() => handleAnswerSelection(option)}
                    className="mr-3"
                  />
                  <span className="text-gray-900 dark:text-white">{option}</span>
                </label>
              ))}
            </div>
          ) : (
            <div className="mb-4">
              <textarea
                value={customAnswer}
                onChange={(e) => setCustomAnswer(e.target.value)}
                placeholder="Enter your custom answer..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          )}

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {currentQuestion.allowCustomAnswer && (
                <button
                  type="button"
                  onClick={() => {
                    setIsCustomMode(!isCustomMode);
                    setSelectedAnswers([]);
                    setCustomAnswer('');
                  }}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  {isCustomMode ? 'Choose from options' : 'Write custom answer'}
                </button>
              )}
            </div>
            
            <div className="flex space-x-2">
              <button
                onClick={handleCancelSession}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleAnswerSubmit}
                disabled={answering || (isCustomMode ? !customAnswer.trim() : selectedAnswers.length === 0)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {answering ? 'Submitting...' : 'Submit Answer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Final Prompt */}
      {finalPrompt && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-green-800 dark:text-green-200 mb-4">
            🎉 Final Prompt Ready!
          </h2>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg">
            <p className="text-gray-900 dark:text-white whitespace-pre-wrap">{finalPrompt.finalPrompt}</p>
          </div>
          <button
            onClick={() => navigator.clipboard.writeText(finalPrompt.finalPrompt)}
            className="mt-4 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            Copy to Clipboard
          </button>
        </div>
      )}

      {/* Start Q&A Button */}
      {session.status === 'active' && !currentQuestion && !finalPrompt && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 text-center">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Ready to start the Q&A loop?
          </h2>
          <button
            onClick={() => {
              // This would trigger the first question - we need to implement this
              // For now, this is a placeholder
            }}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Start Q&A Session
          </button>
        </div>
      )}
    </div>
  );
} 