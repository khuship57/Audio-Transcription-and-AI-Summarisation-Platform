"use client"

import * as React from "react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { CheckCircle, Clock, AlertCircle, XCircle } from 'lucide-react'

interface StatusBadgeProps {
  status: "success" | "pending" | "warning" | "error"
  children: React.ReactNode
  className?: string
}

const statusConfig = {
  success: {
    icon: CheckCircle,
    className: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800",
  },
  pending: {
    icon: Clock,
    className: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800",
  },
  warning: {
    icon: AlertCircle,
    className: "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950 dark:text-orange-300 dark:border-orange-800",
  },
  error: {
    icon: XCircle,
    className: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800",
  },
}

export function StatusBadge({ status, children, className }: StatusBadgeProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <Badge className={cn("flex items-center gap-1.5 px-2.5 py-1", config.className, className)}>
      <Icon className="h-3 w-3" />
      {children}
    </Badge>
  )
}
