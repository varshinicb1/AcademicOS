import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

/**
 * Button. Every state maps to a token -- see docs/design-system.md §7's state
 * matrix. Nothing here is derived or invented at the call site, which is what
 * stops twenty screens acquiring twenty slightly different button styles.
 *
 * Focus is handled by the global `:focus-visible` rule in globals.css, so it is
 * consistent across every control rather than re-specified per component.
 */
export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

const VARIANT: Record<ButtonVariant, string> = {
  primary: cn(
    "bg-btn-primary text-white",
    "hover:bg-btn-primary-hover",
    "active:bg-btn-primary-active active:shadow-[inset_0_1px_2px_rgb(0_0_0/0.18)]",
  ),
  secondary: cn(
    "bg-card text-ink border border-line-strong",
    "hover:bg-canvas hover:border-muted",
    "active:bg-inset",
  ),
  ghost: cn(
    "bg-transparent text-body",
    "hover:bg-inset hover:text-ink",
    "active:bg-line",
  ),
  danger: cn(
    "bg-btn-danger text-white",
    "hover:bg-btn-danger-hover",
    "active:bg-btn-danger-active active:shadow-[inset_0_1px_2px_rgb(0_0_0/0.18)]",
  ),
};

// Height 32 compact / 36 default / 44 touch, per design-system.md §7.
const SIZE: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-9 px-4 text-base",
  lg: "h-11 px-5 text-base",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Swaps the label for a spinner. Width is locked so nothing shifts under the cursor. */
  loading?: boolean;
  /** Required. A control a test cannot address is a control it will find by its text. */
  "data-testid": string;
  children?: ReactNode;
}

/**
 * The class set, exported so a `<Link>` can look like a button without nesting
 * a `<button>` inside an `<a>` -- which is invalid HTML and breaks keyboard
 * activation. Navigation is a link and gets `buttonClasses`; an action is a
 * `<Button>`. Both draw from this one definition, so they cannot drift.
 */
export function buttonClasses({
  variant = "primary",
  size = "md",
  disabled = false,
  className,
}: {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  className?: string;
} = {}): string {
  const base = cn(
    "inline-flex select-none items-center justify-center gap-2 rounded-md font-medium",
    "transition-colors duration-[var(--duration-fast)]",
    SIZE[size],
  );

  if (disabled) {
    // The disabled classes *replace* the variant rather than being appended to
    // it. Appending looked fine and was wrong: `bg-btn-danger` and
    // `bg-btn-disabled` are both single-class utilities, so which one wins is
    // decided by CSS source order, not by their order in this string. That
    // produced a white label on a grey fill -- invisible, measured, fixed.
    return cn(
      base,
      "cursor-not-allowed border border-btn-disabled-line bg-btn-disabled text-btn-disabled-fg",
      className,
    );
  }

  return cn(base, VARIANT[variant], className);
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  className,
  children,
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || loading;
  return (
    <button
      type="button"
      aria-busy={loading || undefined}
      disabled={isDisabled}
      className={buttonClasses({ variant, size, disabled: Boolean(isDisabled), className })}
      {...rest}
    >
      {loading ? (
        <>
          <Spinner />
          <span className="sr-only">Working</span>
          {/* Keeps the label in flow so the button does not resize while loading. */}
          <span className="invisible">{children}</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}

function Spinner() {
  return (
    <span
      aria-hidden="true"
      className="size-4 shrink-0 animate-spin rounded-full border-2 border-current border-t-transparent"
    />
  );
}
