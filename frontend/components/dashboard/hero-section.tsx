"use client"

import { motion } from "framer-motion"
import { FadeIn } from "@/components/animated/fade-in"
import { AuroraBackground } from "@/components/ui/aurora-background"

interface HeroSectionProps {
  onStartTranscribing: () => void
}

export function HeroSection({ onStartTranscribing }: HeroSectionProps) {
  return (
    <AuroraBackground className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Main Content */}
      <div className="relative z-10 text-center px-4 max-w-6xl mx-auto">
        <FadeIn delay={0.4}>
          <div className="mb-8">
            <motion.div 
              initial={{ opacity: 0, y: -30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.8 }}
              className="text-9xl md:text-7xl lg:text-9xl xl:text-8xl font-black tracking-wide leading-none text-transparent bg-clip-text bg-gradient-to-br from-slate-900 via-slate-700 to-slate-600 dark:from-white dark:via-slate-100 dark:to-slate-300"
              style={{ 
                lineHeight: '1.2', 
                letterSpacing: '0.02em',
                paddingTop: '0.1em',
                paddingBottom: '0.1em'
              }}
            >
              MeetingMind
            </motion.div>
          </div>
        </FadeIn>

        <FadeIn delay={0.6}>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.6 }}
            className="text-lg md:text-xl lg:text-2xl text-slate-600 dark:text-slate-300 mb-12 max-w-4xl mx-auto leading-relaxed font-medium tracking-wide"
          >
            Experience the future of audio transcription with AI-powered precision, 
            real-time processing, and intelligent insights that transform how you work with audio content.
          </motion.p>
        </FadeIn>

        <FadeIn delay={0.8}>
          <div className="flex justify-center items-center mb-16">
            <button
              onClick={onStartTranscribing}
              className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 active:scale-95"
            >
              Start Transcribing
            </button>
          </div>
        </FadeIn>
      </div>
    </AuroraBackground>
  )
}