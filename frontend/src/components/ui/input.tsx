import { Input as InputPrimitive } from '@base-ui/react/input';
import * as React from 'react';

import { cn } from '~/lib/utils';

function Input({ className, type, ...props }: React.ComponentProps<'input'>) {
  return (
    <InputPrimitive
      type={type}
      data-slot="input"
      className={cn(
        'w-full rounded-xl border border-border-default bg-surface px-4 py-3 text-base text-fg-strong outline-none transition-colors placeholder:text-fg-muted focus:border-brand focus:ring-1 focus:ring-brand disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    />
  );
}

export { Input };
