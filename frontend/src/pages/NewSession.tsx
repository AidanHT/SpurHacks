import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { Loader2, FileText, Settings, Zap } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { useCreateSessionMutation } from '@/api/sessions';
import { useToast } from '@/hooks/use-toast';

// Form validation schema
const sessionFormSchema = z.object({
  starterPrompt: z
    .string()
    .min(1, 'Starter prompt is required')
    .max(2000, 'Starter prompt must be less than 2000 characters'),
  maxQuestions: z.number().min(1).max(20),
  targetModel: z.string().min(1, 'Please select a target model'),
  tone: z.boolean(), // true = formal, false = friendly
  wordLimit: z.number().min(25).max(300),
  title: z.string().optional(),
});

type SessionFormData = z.infer<typeof sessionFormSchema>;

// Available AI models
const TARGET_MODELS = [
  { value: 'gemini-2.5', label: 'Google Gemini 2.5 (Default)' },
  { value: 'gpt-4', label: 'OpenAI GPT-4' },
  { value: 'gpt-4-turbo', label: 'OpenAI GPT-4 Turbo' },
  { value: 'claude-3-opus', label: 'Anthropic Claude 3 Opus' },
  { value: 'claude-3-sonnet', label: 'Anthropic Claude 3 Sonnet' },
  { value: 'llama-2-70b', label: 'Meta Llama 2 70B' },
] as const;

// Custom hook for debounced values
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default function NewSession(): JSX.Element {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [createSession, { isLoading }] = useCreateSessionMutation();

  const form = useForm<SessionFormData>({
    resolver: zodResolver(sessionFormSchema),
    defaultValues: {
      starterPrompt: '',
      maxQuestions: 10,
      targetModel: 'gemini-2.5',
      tone: false, // false = friendly, true = formal
      wordLimit: 150,
      title: '',
    },
  });

  const watchedValues = form.watch();
  const debouncedPrompt = useDebounce(watchedValues.starterPrompt || '', 300);
  const promptLength = debouncedPrompt.length;
  const isPromptNearLimit = promptLength > 1950;
  const isFormValid = form.formState.isValid && promptLength <= 2000;

  const onSubmit = async (data: SessionFormData) => {
    try {
      const sessionData = {
        title: data.title || undefined,
        starter_prompt: data.starterPrompt,
        max_questions: data.maxQuestions,
        target_model: data.targetModel,
        settings: {
          tone: data.tone ? 'formal' : 'friendly',
          wordLimit: data.wordLimit,
          contextSources: [],
        },
      };

      const result = await createSession(sessionData).unwrap();
      
      toast({
        title: "Session created!",
        description: "Your AI prompting session has been created successfully.",
      });

      // Navigate to the session
      navigate(`/app/${result.id}`);
    } catch (error) {
      console.error('Failed to create session:', error);
      toast({
        title: "Error",
        description: "Failed to create session. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Zap className="h-6 w-6 text-primary" />
              <h1 className="text-xl font-semibold text-foreground">
                Create New Session
              </h1>
            </div>
            <Button
              variant="outline"
              onClick={() => navigate('/')}
            >
              Cancel
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="mx-auto max-w-2xl">
          <div className="mb-8 text-center">
            <h2 className="text-3xl font-bold text-foreground mb-4">
              Start Your AI Prompt Journey
            </h2>
            <p className="text-muted-foreground max-w-lg mx-auto">
              Configure your session settings and let our AI guide you through iterative 
              questioning to craft the perfect prompt.
            </p>
          </div>

          <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                {/* Session Title */}
                <FormField
                  control={form.control}
                  name="title"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="flex items-center space-x-2">
                        <FileText className="h-4 w-4" />
                        <span>Session Title (Optional)</span>
                      </FormLabel>
                      <FormControl>
                        <Input
                          placeholder="e.g., Marketing copy for product launch"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Give your session a descriptive name to find it later.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Starter Prompt */}
                <FormField
                  control={form.control}
                  name="starterPrompt"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="flex items-center justify-between">
                        <span>Starter Prompt *</span>
                        <span 
                          className={`text-xs ${
                            isPromptNearLimit ? 'text-destructive' : 'text-muted-foreground'
                          }`}
                        >
                          {promptLength}/2000
                        </span>
                      </FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Describe what you want to accomplish with AI. Be as specific or general as you like - we'll help refine it together."
                          className="min-h-[120px] resize-none"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        This is your starting point. Our AI will ask targeted questions to help refine and improve this prompt.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Settings Section */}
                <div className="border-t border-border pt-6">
                  <div className="flex items-center space-x-2 mb-4">
                    <Settings className="h-5 w-5 text-primary" />
                    <h3 className="text-lg font-semibold text-foreground">Session Settings</h3>
                  </div>
                  
                  <div className="grid gap-6 md:grid-cols-2">
                    {/* Max Questions */}
                    <FormField
                      control={form.control}
                      name="maxQuestions"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>
                            Max Questions: {field.value}
                          </FormLabel>
                          <FormControl>
                            <Slider
                              min={1}
                              max={20}
                              step={1}
                              value={[field.value]}
                              onValueChange={(vals) => field.onChange(vals[0])}
                              className="w-full"
                            />
                          </FormControl>
                          <FormDescription>
                            How many questions should the AI ask to refine your prompt?
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {/* Target Model */}
                    <FormField
                      control={form.control}
                      name="targetModel"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Target AI Model</FormLabel>
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select a model" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {TARGET_MODELS.map((model) => (
                                <SelectItem key={model.value} value={model.value}>
                                  {model.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormDescription>
                            Which AI model will you use with the final prompt?
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {/* Tone Toggle */}
                    <FormField
                      control={form.control}
                      name="tone"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                          <div className="space-y-0.5">
                            <FormLabel className="text-base">
                              Tone: {field.value ? 'Formal' : 'Friendly'}
                            </FormLabel>
                            <FormDescription>
                              How should the AI interact with you during questioning?
                            </FormDescription>
                          </div>
                          <FormControl>
                            <Switch
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />

                    {/* Word Limit */}
                    <FormField
                      control={form.control}
                      name="wordLimit"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>
                            Final Prompt Length: {field.value} words
                          </FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              min={25}
                              max={300}
                              {...field}
                              onChange={(e) => field.onChange(parseInt(e.target.value) || 25)}
                            />
                          </FormControl>
                          <FormDescription>
                            Target length for your final refined prompt (25-300 words).
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>

                {/* Submit Button */}
                <div className="flex justify-end pt-6 border-t border-border">
                  <Button
                    type="submit"
                    disabled={!isFormValid || isLoading}
                    className="min-w-[140px]"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      'Start Session'
                    )}
                  </Button>
                </div>
              </form>
            </Form>
          </div>
        </div>
      </main>
    </div>
  );
} 