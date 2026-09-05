"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { motion, HTMLMotionProps } from "framer-motion"

interface GlassCardProps extends Omit<HTMLMotionProps<"div">, keyof {
  children: React.ReactNode
  hover?: boolean
  glow?: boolean
}> {
  children: React.ReactNode
  hover?: boolean
  glow?: boolean
}

export function GlassCard({ 
  children, 
  className, 
  hover = true, 
  glow = false, 
  ...props 
}: GlassCardProps) {
  return (
    <motion.div
      whileHover={hover ? { y: -3, scale: 1.01 } : undefined} // Reduced hover effect
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className={cn(
        "relative overflow-hidden rounded-lg border border-border/50 bg-card/50 backdrop-blur-sm", // Changed rounded-2xl to rounded-lg, border-white/10 to border-border/50, bg-white/5 to bg-card/50, backdrop-blur-xl to backdrop-blur-sm
        "shadow-md shadow-black/5", // Softer shadow
        glow && "shadow-primary/10", // Softer glow shadow
        className
      )}
      {...props}
    >
      {/* Removed inner gradient overlay for cleaner look */}
      {children}
    </motion.div>
  )
}
