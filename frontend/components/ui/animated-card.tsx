"use client"

import * as React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface AnimatedCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  hover?: boolean
  delay?: number
}

export function AnimatedCard({ children, className, hover = true, delay = 0, ...props }: AnimatedCardProps) {
  const [isVisible, setIsVisible] = React.useState(false)

  React.useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay)
    return () => clearTimeout(timer)
  }, [delay])

  return (
    <Card
      className={cn(
        "transition-all duration-500 ease-out",
        isVisible ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0",
        hover && "hover:shadow-lg hover:-translate-y-1 hover:scale-[1.02]",
        "border-border/50 bg-card/50 backdrop-blur-sm",
        className
      )}
      {...props}
    >
      {children}
    </Card>
  )
}

export { CardContent, CardDescription, CardHeader, CardTitle }
