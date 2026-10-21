// Utility function tests
import { describe, it, expect } from 'vitest'
import { formatDate, formatDateTime, truncate, getStabilityColor, getStabilityIcon } from '../utils/cn'

describe('formatDate', () => {
  it('formats ISO date string correctly', () => {
    const result = formatDate('2024-01-15T10:30:00Z')
    expect(result).toContain('Jan')
    expect(result).toContain('15')
    expect(result).toContain('2024')
  })

  it('handles different date formats', () => {
    const result = formatDate('2024-12-25')
    expect(result).toContain('Dec')
    expect(result).toContain('25')
    expect(result).toContain('2024')
  })
})

describe('formatDateTime', () => {
  it('includes time component', () => {
    const result = formatDateTime('2024-01-15T10:30:00Z')
    expect(result).toContain('Jan')
    expect(result).toContain('15')
    expect(result).toContain('2024')
    expect(result).toContain(':')
  })
})

describe('truncate', () => {
  it('returns original string if shorter than limit', () => {
    expect(truncate('hello', 10)).toBe('hello')
  })

  it('truncates and adds ellipsis', () => {
    expect(truncate('hello world', 8)).toBe('hello wo...')
  })

  it('handles exact length', () => {
    expect(truncate('hello', 5)).toBe('hello')
  })
})

describe('getStabilityColor', () => {
  it('returns green for stable', () => {
    const result = getStabilityColor('stable')
    expect(result).toContain('green')
  })

  it('returns yellow for experimental', () => {
    const result = getStabilityColor('experimental')
    expect(result).toContain('yellow')
  })

  it('returns red for deprecated', () => {
    const result = getStabilityColor('deprecated')
    expect(result).toContain('red')
  })

  it('returns slate for unknown', () => {
    const result = getStabilityColor('unknown')
    expect(result).toContain('slate')
  })
})

describe('getStabilityIcon', () => {
  it('returns checkmark for stable', () => {
    expect(getStabilityIcon('stable')).toBe('✓')
  })

  it('returns lightning for experimental', () => {
    expect(getStabilityIcon('experimental')).toBe('⚡')
  })

  it('returns warning for deprecated', () => {
    expect(getStabilityIcon('deprecated')).toBe('⚠')
  })

  it('returns question for unknown', () => {
    expect(getStabilityIcon('unknown')).toBe('?')
  })
})