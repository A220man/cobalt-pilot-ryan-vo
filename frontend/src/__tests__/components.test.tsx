// Component tests
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { SearchInput } from '../components/SearchInput'
import { StabilityBadge } from '../components/StabilityBadge'
import { Button } from '../components/Button'
import { PluginCard } from '../components/PluginCard'
import type { PluginListItem } from '../types'

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('SearchInput', () => {
  it('renders with placeholder', () => {
    renderWithRouter(<SearchInput placeholder="Search..." />)
    const input = screen.getByPlaceholderText('Search...')
    expect(input).toBeInTheDocument()
  })

  it('calls onChange with value', () => {
    const handleChange = vi.fn()
    renderWithRouter(<SearchInput onChange={handleChange} />)
    const input = screen.getByRole('searchbox')
    fireEvent.change(input, { target: { value: 'test' } })
    expect(handleChange).toHaveBeenCalledWith(
      expect.objectContaining({ target: expect.objectContaining({ value: 'test' }) })
    )
  })

  it('displays search icon', () => {
    renderWithRouter(<SearchInput />)
    const container = screen.getByRole('searchbox').parentElement
    const svg = container?.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })
})

describe('StabilityBadge', () => {
  it('renders stable badge with green colors', () => {
    renderWithRouter(<StabilityBadge stability="stable" />)
    const badge = screen.getByTestId('stability-badge')
    expect(badge).toHaveClass('bg-green-100')
    expect(badge).toHaveClass('text-green-800')
  })

  it('renders experimental badge with yellow colors', () => {
    renderWithRouter(<StabilityBadge stability="experimental" />)
    const badge = screen.getByTestId('stability-badge')
    expect(badge).toHaveClass('bg-yellow-100')
    expect(badge).toHaveClass('text-yellow-800')
  })

  it('renders deprecated badge with red colors', () => {
    renderWithRouter(<StabilityBadge stability="deprecated" />)
    const badge = screen.getByTestId('stability-badge')
    expect(badge).toHaveClass('bg-red-100')
    expect(badge).toHaveClass('text-red-800')
  })

  it('renders small size correctly', () => {
    renderWithRouter(<StabilityBadge stability="stable" size="sm" />)
    const badge = screen.getByTestId('stability-badge')
    expect(badge).toHaveClass('px-2')
    expect(badge).toHaveClass('py-0.5')
    expect(badge).toHaveClass('text-xs')
  })

  it('hides icon when showIcon=false', () => {
    renderWithRouter(<StabilityBadge stability="stable" showIcon={false} />)
    const badge = screen.getByText('stable')
    expect(badge).not.toContainHTML('✓')
  })
})

describe('Button', () => {
  it('renders with children', () => {
    renderWithRouter(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument()
  })

  it('applies variant classes', () => {
    renderWithRouter(<Button variant="secondary">Secondary</Button>)
    const btn = screen.getByRole('button')
    expect(btn).toHaveClass('bg-slate-100')
  })

  it('applies size classes', () => {
    renderWithRouter(<Button size="lg">Large</Button>)
    const btn = screen.getByRole('button')
    expect(btn).toHaveClass('px-6')
    expect(btn).toHaveClass('py-3')
  })

  it('shows loading spinner when loading', () => {
    renderWithRouter(<Button loading>Loading</Button>)
    const btn = screen.getByRole('button')
    expect(btn).toBeDisabled()
    expect(btn.querySelector('svg')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn()
    renderWithRouter(<Button onClick={handleClick}>Click</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not call onClick when disabled', () => {
    const handleClick = vi.fn()
    renderWithRouter(<Button disabled onClick={handleClick}>Click</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).not.toHaveBeenCalled()
  })
})

describe('PluginCard', () => {
  const mockPlugin: PluginListItem = {
    id: 1,
    slug: 'test-plugin',
    name: 'Test Plugin',
    description: 'A test plugin description',
    plugin_type: 'official',
    repo_path: 'test-plugin',
    license: 'MIT',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
    skills_count: 5,
    commands_count: 3,
    connectors_count: 2,
  }

  it('renders plugin name and slug', () => {
    renderWithRouter(<PluginCard plugin={mockPlugin} />)
    expect(screen.getByText('Test Plugin')).toBeInTheDocument()
    expect(screen.getByText('test-plugin')).toBeInTheDocument()
  })

  it('renders plugin type badge', () => {
    renderWithRouter(<PluginCard plugin={mockPlugin} />)
    expect(screen.getByText('official')).toBeInTheDocument()
  })

  it('renders description', () => {
    renderWithRouter(<PluginCard plugin={mockPlugin} />)
    expect(screen.getByText('A test plugin description')).toBeInTheDocument()
  })

  it('renders skill/command/connector counts', () => {
    renderWithRouter(<PluginCard plugin={mockPlugin} />)
    expect(screen.getByText('5 skills')).toBeInTheDocument()
    expect(screen.getByText('3 commands')).toBeInTheDocument()
    expect(screen.getByText('2 connectors')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn()
    renderWithRouter(<PluginCard plugin={mockPlugin} onClick={handleClick} />)
    fireEvent.click(screen.getByText('Test Plugin'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not have cursor-pointer without onClick', () => {
    renderWithRouter(<PluginCard plugin={mockPlugin} />)
    const card = screen.getByText('Test Plugin').closest('div')
    expect(card).not.toHaveClass('cursor-pointer')
  })
})