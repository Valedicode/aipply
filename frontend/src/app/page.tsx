'use client';

import { Header } from '@/components/Header';
import { ResumeUpload } from '@/components/ResumeUpload';
import { HowItWorks } from '@/components/HowItWorks';
import { ChatContainer } from '@/components/Chat/ChatContainer';
import { useTheme } from '@/hooks/useTheme';
import { useFileUpload } from '@/hooks/useFileUpload';
import { useChat } from '@/hooks/useChat';

export default function Home() {
  const { isDark, toggleTheme } = useTheme();
  const {
    uploadedFile,
    isDragging,
    uploadError,
    fileInputRef,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleFileInputChange,
    handleClickUpload,
    handleRemoveFile,
  } = useFileUpload();
  const {
    messages,
    inputText,
    setInputText,
    isLoading,
    textareaRef,
    messagesEndRef,
    handleSendMessage,
    handleKeyDown,
  } = useChat();

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <Header isDark={isDark} toggleTheme={toggleTheme} />

      {/* Main Content Area */}
      <main className="container mx-auto flex flex-1 flex-col gap-6 p-6">
        <div className="flex flex-1 flex-col gap-6 lg:flex-row">
          {/* Left Sidebar - Upload Section */}
          <aside className="flex flex-col gap-4 lg:w-80">
            <ResumeUpload
              uploadedFile={uploadedFile}
              isDragging={isDragging}
              uploadError={uploadError}
              fileInputRef={fileInputRef}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
              onFileInputChange={handleFileInputChange}
              onClickUpload={handleClickUpload}
              onRemoveFile={handleRemoveFile}
                        />
            <HowItWorks />
          </aside>

          {/* Main Chat Area */}
          <div className="flex flex-1 flex-col gap-4">
            <ChatContainer
              messages={messages}
              inputText={inputText}
              isLoading={isLoading}
              textareaRef={textareaRef}
              messagesEndRef={messagesEndRef}
              onInputChange={setInputText}
                          onKeyDown={handleKeyDown}
              onSendMessage={handleSendMessage}
              onClickUpload={handleClickUpload}
            />
          </div>
        </div>
      </main>
    </div>
  );
}