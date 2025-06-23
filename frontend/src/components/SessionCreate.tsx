import React, { useState } from 'react';
import { useCreateSessionMutation } from '../services/api';
import { useNavigate } from 'react-router-dom';

interface SessionCreateFormData {
  title: string;
  starter_prompt: string;
  max_questions: number;
  target_model: string;
  settings: {
    tone?: string;
    wordLimit?: number;
    contextSources?: string[];
  };
}

const TARGET_MODELS = [
  'gpt-4',
  'gpt-4-turbo', 
  'gpt-3.5-turbo',
  'claude-3-opus',
  'claude-3-sonnet',
  'claude-3-haiku',
  'llama-2-70b',
  'llama-2-13b',
  'gemini-pro'
];

export default function SessionCreate() {
  const navigate = useNavigate();
  const [createSession, { isLoading, error }] = useCreateSessionMutation();
  
  const [formData, setFormData] = useState<SessionCreateFormData>({
    title: '',
    starter_prompt: '',
    max_questions: 10,
    target_model: 'gpt-4',
    settings: {
      tone: 'professional',
      wordLimit: 1000,
      contextSources: []
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const result = await createSession(formData).unwrap();
      navigate(`/app/sessions/${result.id}`);
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const handleInputChange = (field: keyof SessionCreateFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSettingsChange = (field: keyof SessionCreateFormData['settings'], value: any) => {
    setFormData(prev => ({
      ...prev,
      settings: {
        ...prev.settings,
        [field]: value
      }
    }));
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Create New Session
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Title (Optional)
            </label>
            <input
              type="text"
              id="title"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="My AI Prompt Session"
              maxLength={200}
            />
          </div>

          {/* Starter Prompt */}
          <div>
            <label htmlFor="starter_prompt" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Starter Prompt *
            </label>
            <textarea
              id="starter_prompt"
              required
              value={formData.starter_prompt}
              onChange={(e) => handleInputChange('starter_prompt', e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Describe the prompt you want to create or improve..."
              maxLength={5000}
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {formData.starter_prompt.length}/5000 characters
            </p>
          </div>

          {/* Target Model */}
          <div>
            <label htmlFor="target_model" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Target Model *
            </label>
            <select
              id="target_model"
              required
              value={formData.target_model}
              onChange={(e) => handleInputChange('target_model', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            >
              {TARGET_MODELS.map(model => (
                <option key={model} value={model}>
                  {model.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          {/* Max Questions */}
          <div>
            <label htmlFor="max_questions" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Maximum Questions
            </label>
            <input
              type="number"
              id="max_questions"
              min="1"
              max="20"
              value={formData.max_questions}
              onChange={(e) => handleInputChange('max_questions', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Number of AI questions allowed (1-20)
            </p>
          </div>

          {/* Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">Settings</h3>
            
            {/* Tone */}
            <div>
              <label htmlFor="tone" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tone
              </label>
              <select
                id="tone"
                value={formData.settings.tone || ''}
                onChange={(e) => handleSettingsChange('tone', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="professional">Professional</option>
                <option value="casual">Casual</option>
                <option value="formal">Formal</option>
                <option value="creative">Creative</option>
                <option value="technical">Technical</option>
              </select>
            </div>

            {/* Word Limit */}
            <div>
              <label htmlFor="word_limit" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Word Limit
              </label>
              <input
                type="number"
                id="word_limit"
                min="50"
                max="5000"
                value={formData.settings.wordLimit || ''}
                onChange={(e) => handleSettingsChange('wordLimit', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="1000"
              />
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
              <p className="text-red-600 dark:text-red-400 text-sm">
                {'data' in error && error.data && typeof error.data === 'object' && 'detail' in error.data 
                  ? (error.data as any).detail || 'Failed to create session' 
                  : 'Network error'}
              </p>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate('/app/sessions')}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !formData.starter_prompt.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Creating...' : 'Create Session'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 