"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Sidebar, SidebarBody, SidebarLink } from "@/components/ui/sidebar"
import {
  IconUpload,
  IconMicrophone,
  IconUsers,
  IconFileText,
} from "@tabler/icons-react"
import { HeroSection } from "@/components/dashboard/hero-section"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import AudioUpload from "@/components/audio-upload"
import VoiceSampleManager from "@/components/voice-sample-manager"
import SpeakerManager from "@/components/speaker-manager"
import ProcessingResults from "@/components/processing-results"
import { GlassCard } from "@/components/ui/glass-card"
import { FadeIn } from "@/components/animated/fade-in"
import { cn } from "@/lib/utils"
import type { ProcessingResult } from "@/types"

export default function Home() {
  const [activeTab, setActiveTab] = useState("dashboard")
  const [processingResult, setProcessingResult] = useState<ProcessingResult | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [showSidebar, setShowSidebar] = useState(false)

  const links = [
    {
      label: "Upload Audio",
      href: "#",
      icon: (
        <IconUpload className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />
      ),
      key: "upload"
    },
    {
      label: "Voice Samples",
      href: "#",
      icon: (
        <IconMicrophone className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />
      ),
      key: "voice-samples"
    },
    {
      label: "Manage Speakers",
      href: "#",
      icon: (
        <IconUsers className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />
      ),
      key: "speakers"
    },
    {
      label: "Results",
      href: "#",
      icon: (
        <IconFileText className="h-5 w-5 shrink-0 text-neutral-700 dark:text-neutral-200" />
      ),
      key: "results"
    },
  ]

  useEffect(() => {
    // Simulate initial loading
    const timer = setTimeout(() => setIsLoading(false), 1500)
    return () => clearTimeout(timer)
  }, [])

  const handleLinkClick = (key: string) => {
    setActiveTab(key)
  }

  const handleStartTranscribing = () => {
    setShowSidebar(true)
    setActiveTab("upload")
  }

  const handleBackToDashboard = () => {
    setShowSidebar(false)
    setActiveTab("dashboard")
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <LoadingSpinner size="lg" className="mb-4" />
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-foreground text-lg"
          >
            Initializing AI Systems...
          </motion.p>
        </motion.div>
      </div>
    )
  }

  const renderContent = () => {
    switch (activeTab) {
      case "dashboard":
        return (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
          >
            <HeroSection onStartTranscribing={handleStartTranscribing} />
          </motion.div>
        )

      case "upload":
        return (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="py-8 px-4"
          >
            <div className="max-w-4xl mx-auto">
              <FadeIn>
                <GlassCard className="p-8">
                  <div className="text-center mb-8">
                    <motion.h1 
                      className="text-3xl font-bold text-foreground mb-4"
                      initial={{ opacity: 0, y: -20 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      Upload Audio
                    </motion.h1>
                    <motion.p 
                      className="text-muted-foreground"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.2 }}
                    >
                      Transform your audio into intelligent transcriptions
                    </motion.p>
                  </div>
                  <AudioUpload
                    onProcessingStart={() => setIsProcessing(true)}
                    onProcessingComplete={(result) => {
                      setProcessingResult(result)
                      setIsProcessing(false)
                      setActiveTab("results")
                    }}
                    isProcessing={isProcessing}
                  />
                </GlassCard>
              </FadeIn>
            </div>
          </motion.div>
        )

      case "voice-samples":
        return (
          <motion.div
            key="voice-samples"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="py-8 px-4"
          >
            <div className="max-w-4xl mx-auto">
              <FadeIn>
                <GlassCard className="p-8">
                  <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-foreground mb-4">Voice Samples</h1>
                    <p className="text-muted-foreground">Enhance recognition with custom voice samples</p>
                  </div>
                  <VoiceSampleManager />
                </GlassCard>
              </FadeIn>
            </div>
          </motion.div>
        )

      case "speakers":
        return (
          <motion.div
            key="speakers"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="py-8 px-4"
          >
            <div className="max-w-4xl mx-auto">
              <FadeIn>
                <GlassCard className="p-8">
                  <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-foreground mb-4">Manage Speakers</h1>
                    <p className="text-muted-foreground">Configure speaker recognition settings</p>
                  </div>
                  <SpeakerManager />
                </GlassCard>
              </FadeIn>
            </div>
          </motion.div>
        )

      case "results":
        return (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
            className="py-8 px-4"
          >
            <div className="max-w-6xl mx-auto">
              {processingResult ? (
                <ProcessingResults result={processingResult} />
              ) : (
                <FadeIn>
                  <GlassCard className="p-12 text-center">
                    <div className="text-center space-y-4">
                      <motion.div 
                        className="mx-auto h-20 w-20 rounded-md bg-primary flex items-center justify-center mb-6"
                        whileHover={{ rotate: 0, scale: 1.05 }}
                        transition={{ duration: 0.5 }}
                      >
                        <svg
                          className="h-10 w-10 text-primary-foreground"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1.5}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                      </motion.div>
                      <h2 className="text-2xl font-bold text-foreground">No Results Yet</h2>
                      <p className="text-muted-foreground max-w-md mx-auto">
                        Upload and process an audio file to see detailed results and intelligent analysis
                      </p>
                    </div>
                  </GlassCard>
                </FadeIn>
              )}
            </div>
          </motion.div>
        )

      default:
        return null
    }
  }

  const Logo = () => {
    return (
      <a
        href="#"
        className="relative z-20 flex items-center space-x-2 py-1 text-sm font-normal text-black cursor-pointer"
        onClick={handleBackToDashboard}
      >
        <div className="h-5 w-6 shrink-0 rounded-tl-lg rounded-tr-sm rounded-br-lg rounded-bl-sm bg-black dark:bg-white" />
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="font-medium whitespace-pre text-black dark:text-white"
        >
          AI Transcribe
        </motion.span>
      </a>
    )
  }

  const LogoIcon = () => {
    return (
      <a
        href="#"
        className="relative z-20 flex items-center space-x-2 py-1 text-sm font-normal text-black cursor-pointer"
        onClick={handleBackToDashboard}
      >
        <div className="h-5 w-6 shrink-0 rounded-tl-lg rounded-tr-sm rounded-br-lg rounded-bl-sm bg-black dark:bg-white" />
      </a>
    )
  }

  return (
    <div
      className={cn(
        "mx-auto flex w-full max-w-full flex-1 flex-col overflow-hidden bg-gray-100 md:flex-row dark:border-neutral-700 dark:bg-neutral-800",
        "h-screen"
      )}
    >
      {showSidebar && (
        <Sidebar open={sidebarOpen} setOpen={setSidebarOpen}>
          <SidebarBody className="justify-between gap-10">
            <div className="flex flex-1 flex-col overflow-x-hidden overflow-y-auto">
              {sidebarOpen ? <Logo /> : <LogoIcon />}
              <div className="mt-8 flex flex-col gap-2">
                {links.map((link, idx) => (
                  <div key={idx} onClick={() => handleLinkClick(link.key)}>
                    <SidebarLink 
                      link={{
                        ...link,
                        href: "#"
                      }} 
                      className={cn(
                        "cursor-pointer",
                        activeTab === link.key && "bg-neutral-100 dark:bg-neutral-700"
                      )}
                    />
                  </div>
                ))}
              </div>
            </div>
          </SidebarBody>
        </Sidebar>
      )}
      
      {/* Main Content Area */}
      <div className="flex flex-1">
        <div className={cn(
          "flex h-full w-full flex-1 flex-col gap-2 bg-white dark:bg-neutral-900 overflow-y-auto",
          showSidebar ? "rounded-tl-2xl border border-neutral-200 dark:border-neutral-700" : ""
        )}>
          <AnimatePresence mode="wait">
            {renderContent()}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}