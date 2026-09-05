"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { Upload, Loader2, Mic, CheckCircle } from 'lucide-react'
import { uploadVoiceSample } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

export default function VoiceSampleManager() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null) // Corrected: Initial state set to null
  const [speakerName, setSpeakerName] = useState("")
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedSamples, setUploadedSamples] = useState<string[]>([])
  const { toast } = useToast()

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      // Auto-generate speaker name from filename if not provided
      if (!speakerName) {
        const name = file.name
          .split(".")[0]
          .replace(/[-_]/g, " ")
          .replace(/\b\w/g, (l) => l.toUpperCase())
        setSpeakerName(name)
      }
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      toast({
        title: "No file selected",
        description: "Please select a voice sample file",
        variant: "destructive",
      })
      return
    }

    if (!speakerName.trim()) {
      toast({
        title: "Speaker name required",
        description: "Please provide a name for this speaker",
        variant: "destructive",
      })
      return
    }

    setIsUploading(true)

    try {
      const result = await uploadVoiceSample(selectedFile, speakerName.trim())
      setUploadedSamples((prev) => [...prev, result.speaker_name])
      setSelectedFile(null)
      setSpeakerName("")

      // Reset file input
      const fileInput = document.getElementById("voice-sample-file") as HTMLInputElement
      if (fileInput) fileInput.value = ""

      toast({
        title: "Voice sample uploaded",
        description: `Voice sample for ${result.speaker_name} has been added successfully`,
      })
    } catch (error) {
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Failed to upload voice sample",
        variant: "destructive",
      })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card className="border border-border/50 bg-card/50 backdrop-blur-sm">
        <CardContent className="pt-6 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="voice-sample-file" className="text-foreground">Voice Sample File</Label>
            <Input
              id="voice-sample-file"
              type="file"
              accept="audio/*"
              onChange={handleFileSelect}
              disabled={isUploading}
            />
            <p className="text-sm text-muted-foreground">
              Upload a clear audio sample (10-30 seconds) of the speaker for better recognition
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="speaker-name" className="text-foreground">Speaker Name</Label>
            <Input
              id="speaker-name"
              value={speakerName}
              onChange={(e) => setSpeakerName(e.target.value)}
              placeholder="Enter speaker name"
              disabled={isUploading}
            />
          </div>

          <Button
            onClick={handleUpload}
            disabled={!selectedFile || !speakerName.trim() || isUploading}
            className="w-full"
          >
            {isUploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload Voice Sample
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {uploadedSamples.length > 0 && (
        <Card className="border border-border/50 bg-card/50 backdrop-blur-sm">
          <CardContent className="pt-6">
            <h3 className="font-semibold mb-4 flex items-center text-foreground">
              <Mic className="mr-2 h-4 w-4" />
              Recently Uploaded Samples
            </h3>
            <div className="space-y-2">
              {uploadedSamples.map((name, index) => (
                <div key={index} className="flex items-center space-x-2 p-2 bg-emerald-950/20 rounded-lg">
                  <CheckCircle className="h-4 w-4 text-emerald-400" />
                  <span className="text-sm font-medium text-foreground">{name}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
