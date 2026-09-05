"use client"

import type React from "react"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { Upload, Loader2, FileAudio, X } from 'lucide-react'
import { motion } from "framer-motion"
import type { ProcessingResult, ProcessingOptions } from "@/types"
import { uploadAudio } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface AudioUploadProps {
  onProcessingStart: () => void
  onProcessingComplete: (result: ProcessingResult) => void
  isProcessing: boolean
}

export default function AudioUpload({ onProcessingStart, onProcessingComplete, isProcessing }: AudioUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [options, setOptions] = useState<ProcessingOptions>({
    enable_diarization: true,
    enable_speaker_recognition: true,
    whisper_model: "small",
    min_speakers: 2,
    max_speakers: 8,
  })
  const { toast } = useToast()

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      // Validate file type
      if (!file.type.startsWith('audio/')) {
        toast({
          title: "Invalid file type",
          description: "Please select an audio file",
          variant: "destructive",
        })
        return
      }
      setSelectedFile(file)
      console.log("Selected file:", file.name)
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (!file.type.startsWith('audio/')) {
        toast({
          title: "Invalid file type",
          description: "Please select an audio file",
          variant: "destructive",
        })
        return
      }
      setSelectedFile(file)
    }
  }

  const openFileDialog = () => {
    if (!isProcessing) {
      fileInputRef.current?.click()
    }
  }

  const removeFile = () => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      toast({
        title: "No file selected",
        description: "Please select an audio file to upload",
        variant: "destructive",
      })
      return
    }

    onProcessingStart()

    try {
      const result = await uploadAudio(selectedFile, options)
      onProcessingComplete(result)
      toast({
        title: "Processing complete",
        description: "Your audio has been successfully processed",
      })
    } catch (error) {
      toast({
        title: "Processing failed",
        description: error instanceof Error ? error.message : "An error occurred during processing",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* File Upload */}
      <motion.div 
        className="space-y-2"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Label className="text-foreground">Audio File</Label>
        
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          onChange={handleFileSelect}
          className="hidden"
          disabled={isProcessing}
        />
        
        {/* Custom file upload area */}
        <div
          onClick={openFileDialog}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`
            relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-200
            ${dragActive 
              ? 'border-primary bg-primary/10' 
              : selectedFile 
                ? 'border-border/50 bg-card/50' // Subtle background for selected file
                : 'border-border hover:border-primary/50 hover:bg-card/30' // Subtle hover
            }
            ${isProcessing ? 'cursor-not-allowed opacity-50' : ''}
          `}
        >
          {selectedFile ? (
            <motion.div 
              className="space-y-3"
              initial={{ opacity: 0, scale: 0.9 }} // Slightly reduced scale
              animate={{ opacity: 1, scale: 1 }}
            >
              <div className="flex items-center justify-center space-x-2">
                <FileAudio className="h-8 w-8 text-primary" />
              </div>
              <div>
                <p className="font-medium text-foreground">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">{formatFileSize(selectedFile.size)}</p>
              </div>
              <div className="flex items-center justify-center space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    removeFile()
                  }}
                  disabled={isProcessing}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4 mr-1" />
                  Remove
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={openFileDialog}
                  disabled={isProcessing}
                  className="text-primary hover:text-primary/80"
                >
                  <Upload className="h-4 w-4 mr-1" />
                  Change File
                </Button>
              </div>
            </motion.div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-center">
                <Upload className={`h-12 w-12 ${dragActive ? 'text-primary' : 'text-muted-foreground'}`} />
              </div>
              <div>
                <p className="text-lg font-medium text-foreground">
                  {dragActive ? 'Drop your audio file here' : 'Choose an audio file'}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Click to browse or drag and drop your audio file
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  Supports: MP3, WAV, M4A, FLAC, OGG, and other audio formats
                </p>
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* Processing Options */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="border border-border/50 bg-card/50 backdrop-blur-sm">
          <CardContent className="pt-6 space-y-6">
            <h3 className="font-semibold text-lg text-foreground">Processing Options</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex items-center justify-between">
                <Label htmlFor="diarization" className="text-foreground">Speaker Diarization</Label>
                <Switch
                  id="diarization"
                  checked={options.enable_diarization}
                  onCheckedChange={(checked) => setOptions((prev) => ({ ...prev, enable_diarization: checked }))}
                  disabled={isProcessing}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="recognition" className="text-foreground">Speaker Recognition</Label>
                <Switch
                  id="recognition"
                  checked={options.enable_speaker_recognition}
                  onCheckedChange={(checked) => setOptions((prev) => ({ ...prev, enable_speaker_recognition: checked }))}
                  disabled={isProcessing}
                />
              </div>
            </div>

            {/* Whisper Model and Speaker Range on same row with proper alignment */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-end">
              <div className="space-y-2">
                <Label className="text-foreground">Whisper Model</Label>
                <Select
                  value={options.whisper_model}
                  onValueChange={(value) => setOptions((prev) => ({ ...prev, whisper_model: value }))}
                  disabled={isProcessing}
                >
                  <SelectTrigger className="h-10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="tiny">Tiny (fastest)</SelectItem>
                    <SelectItem value="base">Base</SelectItem>
                    <SelectItem value="small">Small (recommended)</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="large">Large (most accurate)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label className="text-foreground">Speaker Range</Label>
                <div className="flex space-x-3">
                  <div className="flex-1">
                    <Label className="text-xs text-muted-foreground">Min</Label>
                    <Input
                      type="number"
                      min="1"
                      max="20"
                      value={options.min_speakers}
                      onChange={(e) => setOptions((prev) => ({ ...prev, min_speakers: Number.parseInt(e.target.value) }))}
                      disabled={isProcessing}
                      className="h-10"
                    />
                  </div>
                  <div className="flex-1">
                    <Label className="text-xs text-muted-foreground">Max</Label>
                    <Input
                      type="number"
                      min="1"
                      max="20"
                      value={options.max_speakers}
                      onChange={(e) => setOptions((prev) => ({ ...prev, max_speakers: Number.parseInt(e.target.value) }))}
                      disabled={isProcessing}
                      className="h-10"
                    />
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Upload Button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <motion.button
          onClick={handleUpload}
          disabled={!selectedFile || isProcessing}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full relative overflow-hidden rounded-md px-8 py-4 bg-primary font-semibold text-primary-foreground shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed" // Simplified button style
        >
          <div className="absolute inset-0 bg-primary/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" /> {/* Subtle hover effect */}
          <span className="relative z-10 flex items-center justify-center gap-2">
            {isProcessing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing Audio...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Process Audio
              </>
            )}
          </span>
        </motion.button>
      </motion.div>
    </div>
  )
}
