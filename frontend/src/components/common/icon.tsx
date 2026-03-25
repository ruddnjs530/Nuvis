import type { ComponentProps } from 'react';
import { HugeiconsIcon } from '@hugeicons/react';

// Figma Design Tokens
export const ICON_SIZES = {
  xs: 14,
  sm: 16,
  md: 24,
  lg: 32,
} as const;

export type IconSize = keyof typeof ICON_SIZES;

export type IconColor = 'brand' | 'default' | 'muted' | 'subtle' | 'currentColor';

export interface CustomIconProps extends Omit<ComponentProps<typeof HugeiconsIcon>, 'size' | 'color' | 'strokeWidth'> {
  icon: ComponentProps<typeof HugeiconsIcon>['icon'];
  size?: IconSize;
  color?: IconColor;
  strokeWidth?: 1.5 | 2;
}

const COLOR_MAP: Record<IconColor, string> = {
  brand: 'var(--color-brand)',
  default: 'var(--color-fg-default)',
  muted: 'var(--color-fg-muted)',
  subtle: 'var(--color-fg-subtle)',
  currentColor: 'currentColor',
};

/**
 * 프로젝트 내 공통 아이콘 컴포넌트.
 */
export default function Icon({
  icon,
  size = 'sm',
  color = 'currentColor',
  strokeWidth = 1.5,
  ...props
}: CustomIconProps) {
  return (
    <HugeiconsIcon
      icon={icon}
      size={ICON_SIZES[size]}
      color={COLOR_MAP[color]}
      strokeWidth={strokeWidth}
      {...props}
    />
  );
}
