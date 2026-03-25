import { cn } from '~/lib/utils';

export interface SpinnerProps {
  className?: string;
  variant?: 'default' | 'white';
}

export default function Spinner({ className, variant = 'default' }: SpinnerProps) {
  return (
    <div
      className={cn(
        'h-10 w-10 animate-spin rounded-full border-4',
        variant === 'default' ? 'border-border-default border-t-brand' : 'border-white/20 border-t-white',
        className,
      )}
    />
  );
}
