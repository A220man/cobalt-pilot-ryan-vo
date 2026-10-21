// StabilityBadge component
import { StabilityLevel } from '../types'
import { cn, getStabilityColor, getStabilityIcon } from '../utils/cn'

interface StabilityBadgeProps {
  stability: StabilityLevel
  size?: 'sm' | 'md'
  showIcon?: boolean
}

export function StabilityBadge({ stability, size = 'md', showIcon = true }: StabilityBadgeProps) {
  const colors = getStabilityColor(stability)
  const icon = getStabilityIcon(stability)

  const sizes = {
    sm: 'px-2 py-0.5 text-xs gap-1',
    md: 'px-2.5 py-1 text-sm gap-1.5',
  }

  return (
    <span data-testid="stability-badge" className={cn('inline-flex items-center font-medium rounded-full', colors, sizes[size])}>
      {showIcon && <span>{icon}</span>}
      <span className="capitalize">{stability}</span>
    </span>
  )
}