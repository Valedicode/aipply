'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/Header';
import { ProgressBreadcrumb } from '@/components/ProgressBreadcrumb';
import { UploadSection } from '@/components/UploadSection';
import { AnalysisLoadingScreen } from '@/components/AnalysisLoadingScreen';
import { ChatContainer } from '@/components/Chat/ChatContainer';
import { useTheme } from '@/hooks/useTheme';
import { useFileUpload } from '@/hooks/useFileUpload';
import { useJobInput } from '@/hooks/useJobInput';
import { useWriterChat } from '@/hooks/useWriterChat';

export default function Home() {
  const { isDark, toggleTheme } = useTheme();
  
  // Flow mode: null = not yet chosen, cv_only = review CV, job_tailoring = tailor to job
  const [flowMode, setFlowMode] = useState<'cv_only' | 'job_tailoring' | null>(null);
  const [jobSkipped, setJobSkipped] = useState(false);
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [chatReady, setChatReady] = useState(false);
  
  // File upload with backend integration
  const {
    uploadedFile,
    cvData,
    isDragging,
    uploadError,
    isUploading,
    needsClarification,
    clarificationQuestions,
    fileInputRef,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleFileInputChange,
    handleClickUpload,
    handleRemoveFile,
    processUploadedFile,
  } = useFileUpload({ 
    sessionId: null, // No longer needed - Writer chat creates its own session
    onCVUploaded: () => {
      console.log('CV uploaded successfully');
    }
  });
  
  // Job input with backend integration
  const {
    jobUrl,
    setJobUrl,
    jobText,
    setJobText,
    jobData,
    isProcessing: isJobProcessing,
    error: jobError,
    urlValidationError,
    textValidationError,
    isValidInput: isValidJobInput,
    submitJob,
    clearError: clearJobError,
    clearJob,
  } = useJobInput({
    sessionId: null, // No longer needed - Writer chat creates its own session
    onJobSubmitted: () => {
      console.log('Job submitted successfully');
    }
  });
  
  // Writer chat - Direct interaction with Writer agent
  const {
    sessionId,
    isInitializing,
    sessionError,
    messages,
    fadingOutMessageId,
    inputText,
    setInputText,
    isLoading,
    chatError,
    textareaRef,
    messagesEndRef,
    handleSendMessage,
    handleKeyDown,
    initializeSession,
  } = useWriterChat({
    cvData,
    jobData,
    flowMode,
  });

  // Handlers for new functionality
  const handleSetFlowMode = (mode: 'cv_only' | 'job_tailoring') => {
    setFlowMode(mode);
    if (mode === 'cv_only') {
      setJobSkipped(true);
    } else {
      setJobSkipped(false);
    }
  };

  const handleSkipJob = () => {
    setJobSkipped(true);
  };

  const handleUnskipJob = () => {
    setJobSkipped(false);
  };

  const handleStartAnalysis = async () => {
    // Immediately swap UI to loading screen
    setAnalysisStarted(true);
    setChatReady(false);

    // Process resume if not already processed
    if (uploadedFile && !cvData) {
      await processUploadedFile();
    }

    // Process job if valid input is provided but not yet processed
    if (isValidJobInput && !jobData && !jobSkipped) {
      await submitJob();
    }
  };

  // Determine if analysis can be started
  const canStartAnalysis = flowMode === 'cv_only'
    ? !!uploadedFile && !isUploading
    : !!uploadedFile && !isUploading && (jobSkipped || isValidJobInput);
  
  // Determine if both uploads are complete and analysis is done
  const inputsReady = !!cvData && (flowMode === 'cv_only' || jobSkipped || !!jobData);
  
  // Initialize Writer chat when CV and optional job data are ready (during "Prepare chat" phase)
  useEffect(() => {
    if (!analysisStarted || !cvData || sessionId || isInitializing) return;
    if (flowMode === null) return;
    
    // cv_only: only CV needed; job_tailoring: need job skipped or job data ready
    const readyToChat = flowMode === 'cv_only'
      ? true
      : (jobSkipped || !!jobData);
    
    if (readyToChat) {
      initializeSession();
    }
  }, [analysisStarted, cvData, jobData, jobSkipped, flowMode, sessionId, isInitializing, initializeSession]);

  // Mark chat as ready when session initialization completes
  useEffect(() => {
    if (!analysisStarted) {
      setChatReady(false);
      return;
    }

    if (!inputsReady) {
      setChatReady(false);
      return;
    }

    // Chat is ready when session is initialized (not initializing and has sessionId)
    if (sessionId && !isInitializing) {
      setChatReady(true);
    } else {
      setChatReady(false);
    }
  }, [analysisStarted, inputsReady, sessionId, isInitializing]);

  const bothUploadsComplete = analysisStarted && chatReady && inputsReady;
  const isAnalyzing = isUploading || isJobProcessing;
  const hasJobInput = isValidJobInput;

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <Header isDark={isDark} toggleTheme={toggleTheme} />

      {/* Main Content Area */}
      <main className="container mx-auto flex flex-1 flex-col gap-6 p-6">
        {/* Session Error Banner */}
        {sessionError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-950/30">
            <div className="flex items-start gap-3">
              <svg
                className="h-5 w-5 flex-shrink-0 text-red-600 dark:text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div className="flex-1">
                <h3 className="font-semibold text-red-900 dark:text-red-100">
                  Connection Error
                </h3>
                <p className="mt-1 text-sm text-red-700 dark:text-red-400">
                  {sessionError}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Session Initializing */}
        {isInitializing && (
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/50 dark:bg-blue-950/30">
            <div className="flex items-center gap-3">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent dark:border-blue-400"></div>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Initializing AI session...
              </p>
            </div>
          </div>
        )}

        {/* Progress Breadcrumb */}
        <div className="mb-6">
          <ProgressBreadcrumb
            resumeUploaded={!!uploadedFile}
            jobUploaded={!!jobData}
            jobSkipped={jobSkipped}
            jobInputValid={isValidJobInput}
            analysisStarted={analysisStarted}
            isAnalyzing={isAnalyzing}
            chatReady={chatReady}
          />
        </div>

        {/* Conditional Content: Upload Section or Chat Interface */}
        <div className="flex flex-1 flex-col">
          {!analysisStarted ? (
            <div className="transition-opacity duration-500 ease-in-out">
              <UploadSection
                flowMode={flowMode}
                onSetFlowMode={handleSetFlowMode}
                uploadedFile={uploadedFile}
                isDragging={isDragging}
                uploadError={uploadError}
                isUploading={isUploading}
                cvData={cvData}
                needsClarification={needsClarification}
                clarificationQuestions={clarificationQuestions}
                fileInputRef={fileInputRef}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onFileInputChange={handleFileInputChange}
                onClickUpload={handleClickUpload}
                onRemoveFile={handleRemoveFile}
                jobUrl={jobUrl}
                setJobUrl={setJobUrl}
                jobText={jobText}
                setJobText={setJobText}
                jobData={jobData}
                isJobProcessing={isJobProcessing}
                jobError={jobError}
                urlValidationError={urlValidationError}
                textValidationError={textValidationError}
                onJobClear={clearJob}
                jobSkipped={jobSkipped}
                onSkipJob={handleSkipJob}
                onUnskipJob={handleUnskipJob}
                onStartAnalysis={handleStartAnalysis}
                analysisStarted={analysisStarted}
                canStartAnalysis={canStartAnalysis}
              />
            </div>
          ) : !bothUploadsComplete ? (
            <div className="flex flex-1 animate-fade-in">
              <AnalysisLoadingScreen
                resumeState={cvData ? 'done' : 'active'}
                jobState={
                  jobSkipped
                    ? 'skipped'
                    : jobData
                      ? 'done'
                      : analysisStarted && cvData && isValidJobInput
                        ? 'active'
                        : 'pending'
                }
                preparingState={
                  cvData && inputsReady 
                    ? (sessionId && !isInitializing ? 'done' : 'active')
                    : 'pending'
                }
              />
            </div>
          ) : (
            <div className="flex flex-1 animate-fade-in">
              <ChatContainer
                messages={messages}
                fadingOutMessageId={fadingOutMessageId}
                inputText={inputText}
                isLoading={isLoading}
                textareaRef={textareaRef}
                messagesEndRef={messagesEndRef}
                onInputChange={setInputText}
                onKeyDown={handleKeyDown}
                onSendMessage={handleSendMessage}
                onClickUpload={handleClickUpload}
                sessionReady={!!sessionId && !isInitializing}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
