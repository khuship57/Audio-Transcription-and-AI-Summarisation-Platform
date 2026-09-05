"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Loader2, Users, UserCheck } from 'lucide-react'
import { getSpeakers, selectSpeakers } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface SpeakersData {
  preloaded_speakers: string[]
  uploaded_speakers: string[]
  active_speakers: string[]
}

export default function SpeakerManager() {
  const [speakers, setSpeakers] = useState<SpeakersData | null>(null)
  const [selectedSpeakers, setSelectedSpeakers] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUpdating, setIsUpdating] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    loadSpeakers()
  }, [])

  const loadSpeakers = async () => {
    try {
      const data = await getSpeakers()
      setSpeakers(data)
      setSelectedSpeakers(data.active_speakers)
    } catch (error) {
      toast({
        title: "Failed to load speakers",
        description: "Could not retrieve speaker information",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSpeakerToggle = (speakerName: string, checked: boolean) => {
    setSelectedSpeakers((prev) => (checked ? [...prev, speakerName] : prev.filter((name) => name !== speakerName)))
  }

  const handleUpdateSelection = async () => {
    setIsUpdating(true)
    try {
      const result = await selectSpeakers(selectedSpeakers)
      setSpeakers((prev) => (prev ? { ...prev, active_speakers: result.active_speakers } : null))
      toast({
        title: "Speakers updated",
        description: `${selectedSpeakers.length} speakers selected for recognition`,
      })
    } catch (error) {
      toast({
        title: "Update failed",
        description: "Could not update speaker selection",
        variant: "destructive",
      })
    } finally {
      setIsUpdating(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-foreground" />
      </div>
    )
  }

  if (!speakers) {
    return <div className="text-center text-muted-foreground">Failed to load speaker information</div>
  }

  const allSpeakers = [...speakers.preloaded_speakers, ...speakers.uploaded_speakers]

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="border border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center text-lg text-foreground">
              <Users className="mr-2 h-5 w-5" />
              Preloaded Speakers
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {speakers.preloaded_speakers.length > 0 ? (
              speakers.preloaded_speakers.map((speaker) => (
                <div key={speaker} className="flex items-center space-x-3">
                  <Checkbox
                    id={`preloaded-${speaker}`}
                    checked={selectedSpeakers.includes(speaker)}
                    onCheckedChange={(checked) => handleSpeakerToggle(speaker, checked as boolean)}
                  />
                  <label htmlFor={`preloaded-${speaker}`} className="flex-1 cursor-pointer text-foreground">
                    {speaker}
                  </label>
                  <Badge variant="secondary">Preloaded</Badge>
                </div>
              ))
            ) : (
              <p className="text-muted-foreground text-sm">No preloaded speakers available</p>
            )}
          </CardContent>
        </Card>

        <Card className="border border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center text-lg text-foreground">
              <UserCheck className="mr-2 h-5 w-5" />
              Uploaded Speakers
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {speakers.uploaded_speakers.length > 0 ? (
              speakers.uploaded_speakers.map((speaker) => (
                <div key={speaker} className="flex items-center space-x-3">
                  <Checkbox
                    id={`uploaded-${speaker}`}
                    checked={selectedSpeakers.includes(speaker)}
                    onCheckedChange={(checked) => handleSpeakerToggle(speaker, checked as boolean)}
                  />
                  <label htmlFor={`uploaded-${speaker}`} className="flex-1 cursor-pointer text-foreground">
                    {speaker}
                  </label>
                  <Badge variant="default">Custom</Badge>
                </div>
              ))
            ) : (
              <p className="text-muted-foreground text-sm">
                No uploaded speakers. Upload voice samples to add custom speakers.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
        <div>
          <p className="font-medium text-foreground">Selected Speakers: {selectedSpeakers.length}</p>
          <p className="text-sm text-muted-foreground">These speakers will be used for recognition during audio processing</p>
        </div>
        <Button onClick={handleUpdateSelection} disabled={isUpdating}>
          {isUpdating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Updating...
            </>
          ) : (
            "Update Selection"
          )}
        </Button>
      </div>
    </div>
  )
}
