import { Switch as SwitchPrimitive } from '@base-ui/react/switch';

import { cn } from '~/lib/utils';

function Switch({
  className,
  size = 'default',
  ...props
}: SwitchPrimitive.Root.Props & {
  size?: 'sm' | 'default';
}) {
  return (
    <SwitchPrimitive.Root
      data-slot="switch"
      data-size={size}
      className={cn(
        'peer group/switch relative inline-flex shrink-0 items-center justify-center rounded-full border border-transparent transition-all outline-none after:absolute after:-inset-x-3 after:-inset-y-2 focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/30 aria-invalid:border-destructive aria-invalid:ring-2 aria-invalid:ring-destructive/20 data-[size=default]:h-[28px] data-[size=default]:w-[50px] data-[size=sm]:h-[16px] data-[size=sm]:w-[28px] dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40 data-checked:bg-brand data-unchecked:bg-border-default/50 dark:data-unchecked:bg-input/80 data-disabled:cursor-not-allowed data-disabled:opacity-50',
        className,
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb
        data-slot="switch-thumb"
        className="pointer-events-none block rounded-full bg-surface shadow-sm ring-0 transition-transform group-data-[size=default]/switch:size-[24px] group-data-[size=sm]/switch:size-3.5 group-data-[size=default]/switch:data-checked:translate-x-[11px] group-data-[size=sm]/switch:data-checked:translate-x-[6px] dark:data-checked:bg-primary-foreground group-data-[size=default]/switch:data-unchecked:translate-x-[-11px] group-data-[size=sm]/switch:data-unchecked:translate-x-[-6px] dark:data-unchecked:bg-foreground"
      />
    </SwitchPrimitive.Root>
  );
}

export { Switch };
