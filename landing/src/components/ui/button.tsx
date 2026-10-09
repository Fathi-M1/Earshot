import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap font-sans font-medium transition-[background-color,opacity,transform] duration-[120ms] ease-[cubic-bezier(0.4,0,0.6,1)] focus-visible:outline-none disabled:pointer-events-none",
  {
    variants: {
      variant: {
        cta: "bg-forest text-paper hover:bg-forest-deep active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-forest focus-visible:ring-offset-2 focus-visible:ring-offset-paper disabled:opacity-[0.42]",
        link: "h-auto rounded-none bg-transparent px-0 text-forest hover:underline hover:[text-underline-offset:3px] active:opacity-70 focus-visible:ring-2 focus-visible:ring-forest focus-visible:ring-offset-2 focus-visible:ring-offset-paper disabled:opacity-[0.42]",
      },
      size: {
        lg: "min-h-11 rounded-pill px-[22px] py-3 text-[17px] leading-none tracking-[-0.01em]",
        sm: "h-6 rounded-pill px-[11px] py-1 text-[12px] leading-none",
        inline: "min-h-0 rounded-none px-0 py-0 text-[17px] leading-[1.38] tracking-[-0.005em]",
      },
    },
    defaultVariants: {
      variant: "cta",
      size: "lg",
    },
  },
);

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };
