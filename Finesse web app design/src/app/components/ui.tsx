import React from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function Card({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("bg-[#251A12] border border-[#3D2B1A] overflow-hidden", className)} {...props}>
      {children}
    </div>
  );
}

export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("px-6 py-5 border-b border-[#3D2B1A]", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ className, children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn("text-lg font-semibold text-[#F0E6D3] leading-none tracking-tight", className)} {...props}>
      {children}
    </h3>
  );
}

export function CardContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-6", className)} {...props}>
      {children}
    </div>
  );
}

export function CardDescription({ className, children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-sm text-[#A89070]", className)} {...props}>
      {children}
    </p>
  );
}

export function CardFooter({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("px-6 py-4 bg-[#2E2016] border-t border-[#3D2B1A] flex items-center", className)} {...props}>
      {children}
    </div>
  );
}

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center font-medium transition-all duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C8A96E] disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97]";

    const variants = {
      primary: "bg-[#C8A96E] text-[#1C1510] hover:bg-[#D4B87A]",
      secondary: "bg-[#2E2016] text-[#F0E6D3] hover:bg-[#3D2B1A]",
      outline: "border border-[#3D2B1A] bg-transparent hover:bg-[#2E2016] text-[#F0E6D3]",
      ghost: "hover:bg-[#2E2016] text-[#F0E6D3]",
      danger: "bg-[#B85C4A] text-[#F0E6D3] hover:bg-[#B85C4A]/90",
    };

    const sizes = {
      sm: "h-8 px-3 text-xs",
      md: "h-10 px-4 py-2 text-sm",
      lg: "h-12 px-8 text-base",
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full border border-[#3D2B1A] bg-[#2E2016] px-3 py-2 text-sm text-[#F0E6D3] placeholder:text-[#A89070]/50 focus:outline-none focus:ring-2 focus:ring-[#C8A96E] focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50 transition-shadow",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export const Label = React.forwardRef<HTMLLabelElement, React.LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn("text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-[#F0E6D3]", className)}
      {...props}
    />
  )
);
Label.displayName = "Label";

export function Badge({ className, variant = "default", children, ...props }: React.HTMLAttributes<HTMLDivElement> & { variant?: "default" | "success" | "warning" | "danger" | "outline" }) {
  const variants = {
    default: "bg-[#2E2016] text-[#F0E6D3]",
    success: "bg-[#7A9E5F]/20 text-[#7A9E5F]",
    warning: "bg-[#C8A96E]/20 text-[#C8A96E]",
    danger: "bg-[#B85C4A]/20 text-[#B85C4A]",
    outline: "border border-[#3D2B1A] text-[#F0E6D3]",
  };

  return (
    <div className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors", variants[variant], className)} {...props}>
      {children}
    </div>
  );
}
