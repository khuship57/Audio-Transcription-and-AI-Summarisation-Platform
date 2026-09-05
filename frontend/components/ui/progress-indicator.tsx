"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface ProgressIndicatorProps {
  value: number
  max?: number
  className?: string
  showPercentage?: boolean
}

export function ProgressIndicator({ value, max = 100, className, showPercentage = false }: ProgressIndicatorProps) {
  const percentage = Math.min((value / max) * 100, 100)

  return (
    <div className={cn("w-full space-y-2", className)}>
      <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full bg-primary transition-all duration-500 ease-out" // Changed gradient to solid primary color
          style={{ width: `${percentage}%` }}
        />
        {/* Removed shimmer effect */}
      </div>
      {showPercentage && (
        <div className="text-right text-sm text-muted-foreground">
          {Math.round(percentage)}%
        </div>
      )}
    </div>
  )
}
