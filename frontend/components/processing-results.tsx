"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Download, FileText, Users, Clock, BarChart3 } from 'lucide-react'
import { motion } from "framer-motion"
import type { ProcessingResult } from "@/types"
import { downloadPDF } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface ProcessingResultsProps {
  result: ProcessingResult
}

export default function ProcessingResults({ result }: ProcessingResultsProps) {
  const [isDownloading, setIsDownloading] = useState(false)
  const { toast } = useToast()

  const handleDownloadPDF = async () => {
    setIsDownloading(true)
    try {
      await downloadPDF(result.summary)
      toast({
        title: "PDF downloaded",
        description: "Meeting summary has been downloaded successfully",
      })
    } catch (error) {
      toast({
        title: "Download failed",
        description: "Could not download PDF",
        variant: "destructive",
      })
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { icon: Clock, label: "Duration", value: result.duration, color: "bg-blue-500" }, // Changed to solid color
          { icon: Users, label: "Speakers", value: result.speakers_detected.toString(), color: "bg-green-500" }, // Changed to solid color
          { icon: BarChart3, label: "Topics", value: result.processing_stats.topics_identified.toString(), color: "bg-purple-500" }, // Changed to solid color
          { icon: FileText, label: "Chunks", value: result.processing_stats.unique_chunks.toString(), color: "bg-orange-500" }, // Changed to solid color
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -3, scale: 1.01 }} // Reduced hover effect
          >
            <Card className="border border-border/50 bg-card/50 backdrop-blur-sm shadow-sm dark:shadow-none">
              <CardContent className="pt-6">
                <div className="flex items-center space-x-2">
                  <div className={`p-2 rounded-md ${stat.color} shadow-sm`}> {/* Changed rounded-lg to rounded-md */}
                    <stat.icon className="h-4 w-4 text-primary-foreground" /> {/* Changed to primary-foreground */}
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-foreground">{stat.value}</p>
                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Main Results */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <Card className="border border-border/50 bg-card/50 backdrop-blur-sm shadow-sm dark:shadow-none">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center text-foreground">
                <FileText className="mr-2 h-5 w-5" />
                Processing Results
              </CardTitle>
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}> {/* Reduced hover effect */}
                <Button onClick={handleDownloadPDF} disabled={isDownloading} variant="outline">
                  {isDownloading ? (
                    <>
                      <Download className="mr-2 h-4 w-4 animate-pulse" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Download className="mr-2 h-4 w-4" />
                      Download PDF
                    </>
                  )}
                </Button>
              </motion.div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="summary" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="transcript">Full Transcript</TabsTrigger>
                <TabsTrigger value="stats">Processing Stats</TabsTrigger>
              </TabsList>

              <TabsContent value="summary" className="mt-4">
                <ScrollArea className="h-[600px] w-full rounded-md border border-border/30 p-4 bg-muted/50">
                  <div className="prose max-w-none dark:prose-invert">
                    <div
                      className="whitespace-pre-wrap text-sm leading-relaxed text-foreground"
                      dangerouslySetInnerHTML={{ __html: result.summary.replace(/\n/g, "<br>") }}
                    />
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="transcript" className="mt-4">
                <ScrollArea className="h-[600px] w-full rounded-md border p-4">
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <p className="whitespace-pre-wrap text-sm leading-relaxed font-mono text-foreground">
                      {result.transcript}
                    </p>
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="stats" className="mt-4">
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-muted/50 rounded-lg">
                      <p className="text-2xl font-bold text-foreground">
                        {result.processing_stats.original_chunks}
                      </p>
                      <p className="text-sm text-muted-foreground">Original Chunks</p>
                    </div>
                    <div className="text-center p-4 bg-muted/50 rounded-lg">
                      <p className="text-2xl font-bold text-foreground">
                        {result.processing_stats.unique_chunks}
                      </p>
                      <p className="text-sm text-muted-foreground">Unique Chunks</p>
                    </div>
                    <div className="text-center p-4 bg-muted/50 rounded-lg">
                      <p className="text-2xl font-bold text-foreground">
                        {result.processing_stats.topics_identified}
                      </p>
                      <p className="text-sm text-muted-foreground">Topics Identified</p>
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <h3 className="font-semibold text-foreground">Processing Summary</h3>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <p>• Duration: {result.duration}</p>
                      <p>• Speakers detected: {result.speakers_detected}</p>
                      <p>• Processing completed successfully</p>
                      <p>• Summary generated with {result.processing_stats.topics_identified} main topics</p>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
