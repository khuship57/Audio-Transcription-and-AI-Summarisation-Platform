"use client"

import { motion } from "framer-motion"
import { FadeIn } from "@/components/animated/fade-in"
import { GlassCard } from "@/components/ui/glass-card"
import { AnimatedCounter } from "@/components/ui/animated-counter"
import { Zap, Heart, Shield, Target } from 'lucide-react'

export function StatsSection() {
  const stats = [
    { icon: Zap, label: "Processing Speed", value: 95, suffix: "%", color: "bg-blue-500" }, // Changed to solid color
    { icon: Heart, label: "User Satisfaction", value: 98, suffix: "%", color: "bg-purple-500" }, // Changed to solid color
    { icon: Shield, label: "Uptime", value: 99, suffix: "%", color: "bg-green-500" }, // Changed to solid color
    { icon: Target, label: "Accuracy Rate", value: 97, suffix: "%", color: "bg-orange-500" }, // Changed to solid color
  ]

  return (
    <section className="py-20 px-4 bg-background"> {/* Ensure consistent background */}
      <div className="max-w-7xl mx-auto">
        <FadeIn>
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-foreground"> {/* Removed text gradient */}
              Performance Metrics
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto"> {/* Changed text color */}
              Real-time performance indicators showcasing our commitment to excellence, 
              reliability, and user satisfaction across all platform operations.
            </p>
          </div>
        </FadeIn>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <FadeIn key={stat.label} delay={index * 0.1}>
              <motion.div
                whileHover={{ 
                  y: -5, // Reduced hover effect
                  rotateY: 0, // Removed rotateY
                  scale: 1.01, // Reduced scale
                  boxShadow: "0 15px 30px rgba(0,0,0,0.08)" // Softer shadow
                }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
              >
                <GlassCard className="p-6 text-center group hover:bg-card/60 transition-all duration-300 border border-border/50"> {/* Adjusted hover background and border */}
                  <div className="mb-4">
                    <motion.div 
                      className={`inline-flex items-center justify-center w-16 h-16 rounded-full ${stat.color} p-0.5`} // Used solid color
                      whileHover={{ rotate: 0, scale: 1.05 }} // Reduced hover effect
                      transition={{ duration: 0.5 }}
                    >
                      <div className="flex items-center justify-center w-full h-full rounded-full bg-background/80"> {/* Changed to background */}
                        <stat.icon className="h-7 w-7 text-primary-foreground" /> {/* Changed to primary-foreground */}
                      </div>
                    </motion.div>
                  </div>
                  <div className="text-3xl font-bold text-foreground mb-2"> {/* Changed text color */}
                    <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                  </div>
                  <p className="text-muted-foreground font-medium">{stat.label}</p> {/* Changed text color */}
                </GlassCard>
              </motion.div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}
