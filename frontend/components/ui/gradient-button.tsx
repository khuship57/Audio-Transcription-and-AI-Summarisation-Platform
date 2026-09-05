"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { motion, HTMLMotionProps } from "framer-motion"

type ButtonVariant = "primary" | "secondary" | "danger"
type ButtonSize = "sm" | "md" | "lg"

interface GradientButtonProps extends Omit<HTMLMotionProps<"button">, "children"> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  children: React.ReactNode
}

// Updated variants for a more subtle, professional look
const variants = {
  primary: "bg-primary hover:bg-primary/90", // Use primary color directly
  secondary: "bg-secondary hover:bg-secondary/80",
  danger: "bg-destructive hover:bg-destructive/90",
}

const sizes = {
  sm: "px-4 py-2 text-sm",
  md: "px-6 py-3 text-base",
  lg: "px-8 py-4 text-lg",
}

export function GradientButton({
  variant = "primary",
  size = "md",
  loading = false,
  children,
  className,
  disabled,
  ...props
}: GradientButtonProps) {
  return (
    <motion.button
      whileHover={disabled ? undefined : { scale: 1.02 }} // Slightly reduced hover scale
      whileTap={disabled ? undefined : { scale: 0.98 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className={cn(
        "relative overflow-hidden rounded-md font-semibold text-primary-foreground transition-all duration-300", // Changed rounded-xl to rounded-md, text-white to text-primary-foreground
        "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2", // Adjusted ring focus
        "disabled:opacity-50 disabled:cursor-not-allowed",
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {children}
    </motion.button>
  )
}
