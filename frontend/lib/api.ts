import type {
  ProcessingOptions,
  ProcessingResult,
  VoiceSampleResult,
  SpeakersData,
  SpeakerSelectionResult,
} from "@/types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5328"

console.log("🔧 API Base URL:", API_BASE_URL); // Debug API URL

class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message)
    this.name = "APIError"
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  console.log("📡 Response received:", {
    status: response.status,
    statusText: response.statusText,
    url: response.url,
    headers: Object.fromEntries(response.headers.entries())
  });

  if (!response.ok) {
    console.error("❌ Response not OK, attempting to parse error");
    
    let errorData;
    try {
      const responseText = await response.text();
      console.error("🔍 Raw error response:", responseText);
      
      try {
        errorData = JSON.parse(responseText);
        console.error("📋 Parsed error data:", errorData);
      } catch (jsonError) {
        console.error("⚠️ Could not parse error response as JSON:", jsonError);
        errorData = { error: responseText || "Unknown error" };
      }
    } catch (textError) {
      console.error("💥 Could not read response text:", textError);
      errorData = { error: "Could not read error response" };
    }
    
    const errorMessage = errorData.error || `HTTP ${response.status}: ${response.statusText}`;
    console.error("🚨 Throwing APIError:", errorMessage);
    throw new APIError(errorMessage, response.status);
  }
  
  try {
    const jsonData = await response.json();
    console.log("✅ Successfully parsed response JSON");
    return jsonData;
  } catch (parseError) {
    console.error("💥 Failed to parse successful response as JSON:", parseError);
    throw new APIError("Invalid JSON response from server");
  }
}

export async function uploadAudio(file: File, options: ProcessingOptions): Promise<ProcessingResult> {
  console.log("🚀 Starting uploadAudio");
  console.log("📁 File details:", {
    name: file.name,
    size: file.size,
    type: file.type,
    lastModified: new Date(file.lastModified).toISOString()
  });
  console.log("⚙️ Processing options:", options);
  console.log("🌐 API Base URL:", API_BASE_URL);

  // Validate file
  if (!file || file.size === 0) {
    console.error("❌ Invalid file:", file);
    throw new APIError("Invalid or empty file");
  }

  try {
    const formData = new FormData();
    formData.append("audio", file);
    formData.append("enable_diarization", options.enable_diarization.toString());
    formData.append("enable_speaker_recognition", options.enable_speaker_recognition.toString());
    formData.append("whisper_model", options.whisper_model);
    formData.append("min_speakers", options.min_speakers.toString());
    formData.append("max_speakers", options.max_speakers.toString());

    console.log("📋 FormData contents:");
    Array.from(formData.entries()).forEach(([key, value]) => {
      if (value instanceof File) {
        console.log(`  ${key}: File(${value.name}, ${value.size} bytes, ${value.type})`);
      } else {
        console.log(`  ${key}: ${value}`);
      }
    });

    const url = `${API_BASE_URL}/api/upload-audio`;
    console.log("🔗 Request URL:", url);

    console.log("📤 Making fetch request...");
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    console.log("📥 Fetch completed, processing response...");
    const result = await handleResponse<ProcessingResult>(response);
    console.log("✅ uploadAudio completed successfully");
    return result;

  } catch (error) {
    console.error("💥 uploadAudio failed:", error);
    
    if (error instanceof TypeError) {
      if (error.message.includes('fetch')) {
        console.error("🌐 Network error detected");
        throw new APIError(`Network error: Cannot connect to server at ${API_BASE_URL}. Please check if the server is running.`);
      }
    }
    
    // Re-throw APIError as-is, wrap other errors
    if (error instanceof APIError) {
      throw error;
    } else {
      throw new APIError(`Unexpected error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}

export async function uploadVoiceSample(file: File, speakerName: string): Promise<VoiceSampleResult> {
  console.log("🎤 Starting uploadVoiceSample");
  const formData = new FormData()
  formData.append("voice_sample", file)
  formData.append("speaker_name", speakerName)

  const response = await fetch(`${API_BASE_URL}/api/upload-voice-sample`, {
    method: "POST",
    body: formData,
  })

  return handleResponse<VoiceSampleResult>(response)
}

export async function getSpeakers(): Promise<SpeakersData> {
  console.log("👥 Getting speakers");
  const response = await fetch(`${API_BASE_URL}/api/speakers`)
  return handleResponse<SpeakersData>(response)
}

export async function selectSpeakers(selectedSpeakers: string[]): Promise<SpeakerSelectionResult> {
  console.log("✅ Selecting speakers:", selectedSpeakers);
  const response = await fetch(`${API_BASE_URL}/api/speakers/select`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ selected_speakers: selectedSpeakers }),
  })

  return handleResponse<SpeakerSelectionResult>(response)
}

export async function downloadPDF(markdownContent: string): Promise<void> {
  console.log("📄 Downloading PDF");
  const response = await fetch(`${API_BASE_URL}/api/download-pdf`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ markdown_content: markdownContent }),
  })

  if (!response.ok) {
    throw new APIError("Failed to download PDF")
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.style.display = "none"
  a.href = url
  a.download = "meeting_summary.pdf"
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

export async function checkHealth(): Promise<{ status: string; models_loaded: boolean; ai_refining_available: boolean }> {
  console.log("🏥 Checking server health");
  
  try {
    const url = `${API_BASE_URL}/api/health`;
    console.log("🔗 Health check URL:", url);
    
    const response = await fetch(url);
    console.log("📡 Health check response:", response.status, response.statusText);
    
    const result = await handleResponse<{ status: string; models_loaded: boolean; ai_refining_available: boolean }>(response);
    console.log("✅ Health check result:", result);
    return result;
  } catch (error) {
    console.error("💥 Health check failed:", error);
    throw error;
  }
}

// Add this new function for testing
export async function testUploadEndpoint() {
  console.log("🧪 Testing upload endpoint connectivity");
  return await checkHealth();
}