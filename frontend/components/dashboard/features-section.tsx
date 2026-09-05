"use client"

import { motion } from "framer-motion"
import { FadeIn } from "@/components/animated/fade-in"
import { GlassCard } from "@/components/ui/glass-card"
import { Mic, Brain, Zap, Shield, Globe, FileText, Users } from 'lucide-react'

export function FeaturesSection() {
  const features = [
    {
      icon: Mic,
      title: "Real-time Transcription",
      description: "Convert speech to text instantly with industry-leading accuracy and speed.",
      gradient: "bg-blue-500", // Changed to solid color
    },
    {
      icon: Brain,
      title: "AI-Powered Analysis",
      description: "Advanced machine learning algorithms provide intelligent insights and summaries.",
      gradient: "bg-purple-500", // Changed to solid color
    },
    {
      icon: Users,
      title: "Speaker Identification",
      description: "Automatically identify and separate different speakers in your audio content.",
      gradient: "bg-green-500", // Changed to solid color
    },
    {
      icon: FileText,
      title: "Smart Summaries",
      description: "Generate concise, actionable summaries from lengthy audio recordings.",
      gradient: "bg-orange-500", // Changed to solid color
    },
    {
      icon: Globe,
      title: "Multi-language Support",
      description: "Support for 50+ languages with native-level transcription accuracy.",
      gradient: "bg-teal-500", // Changed to solid color
    },
    {
      icon: Shield,
      title: "Enterprise Security",
      description: "Bank-level encryption and compliance with industry security standards.",
      gradient: "bg-indigo-500", // Changed to solid color
    },
  ]

  return (
    <section className="py-20 px-4 bg-background"> {/* Ensure consistent background */}
      <div className="max-w-7xl mx-auto">
        <FadeIn>
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-foreground"> {/* Removed text gradient */}
              Powerful Features
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto"> {/* Changed text color */}
              Everything you need to transform your audio content into actionable insights, 
              powered by cutting-edge AI technology.
            </p>
          </div>
        </FadeIn>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <FadeIn key={feature.title} delay={index * 0.1}>
              <motion.div
                whileHover={{ 
                  y: -5, // Reduced hover effect
                  rotateX: 0, // Removed rotateX
                  rotateY: 0, // Removed rotateY
                  scale: 1.01, // Reduced scale
                  boxShadow: "0 15px 30px rgba(0,0,0,0.08)" // Softer shadow
                }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
              >
                <GlassCard className="p-8 h-full group hover:bg-card/60 transition-all duration-500 border border-border/50"> {/* Adjusted hover background and border */}
                  <div className="mb-6">
                    <motion.div 
                      className={`inline-flex items-center justify-center w-16 h-16 rounded-lg ${feature.gradient} p-0.5`} // Changed rounded-2xl to rounded-lg, used solid color
                      whileHover={{ 
                        rotate: 0, // Removed rotate
                        scale: 1.05 // Reduced scale
                      }}
                      transition={{ duration: 0.3 }} // Reduced duration
                    >
                      <div className="flex items-center justify-center w-full h-full rounded-lg bg-background/80 group-hover:bg-background/90 transition-colors"> {/* Changed rounded-2xl to rounded-lg, adjusted background */}
                        <feature.icon className="h-8 w-8 text-primary-foreground group-hover:scale-100 transition-transform" /> {/* Changed color, removed scale */}
                      </div>
                    </motion.div>
                  </div>
                  <h3 className="text-xl font-bold text-foreground mb-4 group-hover:text-primary transition-colors"> {/* Changed text color, adjusted hover color */}
                    {feature.title}
                  </h3>
                  <p className="text-muted-foreground leading-relaxed group-hover:text-foreground transition-colors"> {/* Changed text color, adjusted hover color */}
                    {feature.description}
                  </p>
                </GlassCard>
              </motion.div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}
