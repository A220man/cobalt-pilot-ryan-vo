import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import type { LLMExplanationRequest, LLMExplanationResponse } from '../types'
import { Button } from './Button'

interface LLMExplanationProps {
  skillSlug: string
  pluginSlug: string
  skillName?: string
  skillDescription?: string
}

export function LLMExplanation({ skillSlug, pluginSlug, skillName, skillDescription }: LLMExplanationProps) {
  const [explanation, setExplanation] = useState<LLMExplanationResponse | null>(null)
  const [question, setQuestion] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)

  const mutation = useMutation({
    mutationFn: (req: LLMExplanationRequest) => api.generateExplanation(req),
    onSuccess: (data) => {
      setExplanation(data)
      setIsExpanded(true)
    },
    onError: (error) => {
      console.error('Failed to generate explanation:', error)
      setExplanation({
        explanation: `Failed to generate explanation: ${error instanceof Error ? error.message : 'Unknown error'}`,
        provider: 'unknown',
        model: 'unknown',
        advisory: true,
        disclaimer: 'This explanation is AI-generated and advisory only. Verify against official documentation.',
      })
      setIsExpanded(true)
    },
  })

  const handleGenerate = () => {
    mutation.mutate({
      skill_slug: skillSlug,
      plugin_slug: pluginSlug,
      question: question || undefined,
      context: skillDescription ? `Skill description: ${skillDescription}` : undefined,
    })
  }

  const handleRegenerate = () => {
    mutation.mutate({
      skill_slug: skillSlug,
      plugin_slug: pluginSlug,
      question: question || undefined,
      context: skillDescription ? `Skill description: ${skillDescription}` : undefined,
    })
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium text-gray-900">AI Explanation</h4>
        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">Advisory</span>
      </div>

      {!isExpanded ? (
        <div className="text-center py-4">
          <p className="text-sm text-gray-600 mb-3">
            Get an AI-generated explanation of <strong>{skillName || skillSlug}</strong>
          </p>
          <div className="space-y-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Optional: specific question about this skill"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <Button onClick={handleGenerate} disabled={mutation.isPending}>
              {mutation.isPending ? 'Generating...' : 'Generate Explanation'}
            </Button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Uses configured LLM provider. Requires API key in backend settings.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {explanation && (
            <div className="prose prose-sm max-w-none bg-white p-3 rounded border">
              {explanation.explanation.split('\n').map((paragraph, i) => (
                <p key={i} className="text-gray-800">{paragraph}</p>
              ))}
            </div>
          )}

          <div className="border-t pt-3">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
              <span>Provider: {explanation?.provider} | Model: {explanation?.model}</span>
              <span className="text-amber-600">⚠ {explanation?.disclaimer}</span>
            </div>

            <div className="space-y-2">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a follow-up question..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex gap-2">
                <Button onClick={handleRegenerate} disabled={mutation.isPending} variant="secondary">
                  {mutation.isPending ? 'Regenerating...' : 'Ask / Regenerate'}
                </Button>
                <Button onClick={() => setIsExpanded(false)} variant="ghost" size="sm">
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
