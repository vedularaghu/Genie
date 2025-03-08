import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState(null);
  const [timeout, setTimeout] = useState(30); // Default timeout of 30 seconds
  const [showSettings, setShowSettings] = useState(false);
  const fileInputRef = useRef(null);
  const chatContainerRef = useRef(null);
  const textareaRef = useRef(null);

  // Replace the Logo component with a Font Awesome brain icon
  const BrainIcon = ({ size = 28, color = '#10a37f' }) => (
    <svg width={size} height={size} viewBox="0 0 512 512" fill={color} xmlns="http://www.w3.org/2000/svg">
      <path d="M184 0C214.9 0 240 25.07 240 56V456C240 486.9 214.9 512 184 512H56C25.07 512 0 486.9 0 456V56C0 25.07 25.07 0 56 0H184zM184 56H56V456H184V56zM336 0H464C494.9 0 520 25.07 520 56V456C520 486.9 494.9 512 464 512H336C305.1 512 280 486.9 280 456V56C280 25.07 305.1 0 336 0zM336 56V456H464V56H336zM208 160H48V96H208V160zM48 224H208V288H48V224zM208 352H48V416H208V352zM304 160H464V96H304V160zM464 224H304V288H464V224zM304 352H464V416H304V352z"/>
    </svg>
  );

  // Icons for the UI
  const FileIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M16 13H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M16 17H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M10 9H9H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  const UploadIcon = () => (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M17 8L12 3L7 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 3V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  const SendIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  const TrashIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M3 6H5H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  const UserIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 11C14.2091 11 16 9.20914 16 7C16 4.79086 14.2091 3 12 3C9.79086 3 8 4.79086 8 7C8 9.20914 9.79086 11 12 11Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  const AssistantIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 16V12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 8H12.01" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  const PlusIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 5V19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  const SettingsIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M19.4 15C19.2669 15.3016 19.2272 15.6362 19.286 15.9606C19.3448 16.285 19.4995 16.5843 19.73 16.82L19.79 16.88C19.976 17.0657 20.1235 17.2863 20.2241 17.5291C20.3248 17.7719 20.3766 18.0322 20.3766 18.295C20.3766 18.5578 20.3248 18.8181 20.2241 19.0609C20.1235 19.3037 19.976 19.5243 19.79 19.71C19.6043 19.896 19.3837 20.0435 19.1409 20.1441C18.8981 20.2448 18.6378 20.2966 18.375 20.2966C18.1122 20.2966 17.8519 20.2448 17.6091 20.1441C17.3663 20.0435 17.1457 19.896 16.96 19.71L16.9 19.65C16.6643 19.4195 16.365 19.2648 16.0406 19.206C15.7162 19.1472 15.3816 19.1869 15.08 19.32C14.7842 19.4468 14.532 19.6572 14.3543 19.9255C14.1766 20.1938 14.0813 20.5082 14.08 20.83V21C14.08 21.5304 13.8693 22.0391 13.4942 22.4142C13.1191 22.7893 12.6104 23 12.08 23C11.5496 23 11.0409 22.7893 10.6658 22.4142C10.2907 22.0391 10.08 21.5304 10.08 21V20.91C10.0723 20.579 9.96512 20.258 9.77251 19.9887C9.5799 19.7194 9.31074 19.5143 9 19.4C8.69838 19.2669 8.36381 19.2272 8.03941 19.286C7.71502 19.3448 7.41568 19.4995 7.18 19.73L7.12 19.79C6.93425 19.976 6.71368 20.1235 6.47088 20.2241C6.22808 20.3248 5.96783 20.3766 5.705 20.3766C5.44217 20.3766 5.18192 20.3248 4.93912 20.2241C4.69632 20.1235 4.47575 19.976 4.29 19.79C4.10405 19.6043 3.95653 19.3837 3.85588 19.1409C3.75523 18.8981 3.70343 18.6378 3.70343 18.375C3.70343 18.1122 3.75523 17.8519 3.85588 17.6091C3.95653 17.3663 4.10405 17.1457 4.29 16.96L4.35 16.9C4.58054 16.6643 4.73519 16.365 4.794 16.0406C4.85282 15.7162 4.81312 15.3816 4.68 15.08C4.55324 14.7842 4.34276 14.532 4.07447 14.3543C3.80618 14.1766 3.49179 14.0813 3.17 14.08H3C2.46957 14.08 1.96086 13.8693 1.58579 13.4942C1.21071 13.1191 1 12.6104 1 12.08C1 11.5496 1.21071 11.0409 1.58579 10.6658C1.96086 10.2907 2.46957 10.08 3 10.08H3.09C3.42099 10.0723 3.742 9.96512 4.0113 9.77251C4.28059 9.5799 4.48572 9.31074 4.6 9C4.73312 8.69838 4.77282 8.36381 4.714 8.03941C4.65519 7.71502 4.50054 7.41568 4.27 7.18L4.21 7.12C4.02405 6.93425 3.87653 6.71368 3.77588 6.47088C3.67523 6.22808 3.62343 5.96783 3.62343 5.705C3.62343 5.44217 3.67523 5.18192 3.77588 4.93912C3.87653 4.69632 4.02405 4.47575 4.21 4.29C4.39575 4.10405 4.61632 3.95653 4.85912 3.85588C5.10192 3.75523 5.36217 3.70343 5.625 3.70343C5.88783 3.70343 6.14808 3.75523 6.39088 3.85588C6.63368 3.95653 6.85425 4.10405 7.04 4.29L7.1 4.35C7.33568 4.58054 7.63502 4.73519 7.95941 4.794C8.28381 4.85282 8.61838 4.81312 8.92 4.68H9C9.29577 4.55324 9.54802 4.34276 9.72569 4.07447C9.90337 3.80618 9.99872 3.49179 10 3.17V3C10 2.46957 10.2107 1.96086 10.5858 1.58579C10.9609 1.21071 11.4696 1 12 1C12.5304 1 13.0391 1.21071 13.4142 1.58579C13.7893 1.96086 14 2.46957 14 3V3.09C14.0013 3.41179 14.0966 3.72618 14.2743 3.99447C14.452 4.26276 14.7042 4.47324 15 4.6C15.3016 4.73312 15.6362 4.77282 15.9606 4.714C16.285 4.65519 16.5843 4.50054 16.82 4.27L16.88 4.21C17.0657 4.02405 17.2863 3.87653 17.5291 3.77588C17.7719 3.67523 18.0322 3.62343 18.295 3.62343C18.5578 3.62343 18.8181 3.67523 19.0609 3.77588C19.3037 3.87653 19.5243 4.02405 19.71 4.21C19.896 4.39575 20.0435 4.61632 20.1441 4.85912C20.2448 5.10192 20.2966 5.36217 20.2966 5.625C20.2966 5.88783 20.2448 6.14808 20.1441 6.39088C20.0435 6.63368 19.896 6.85425 19.71 7.04L19.65 7.1C19.4195 7.33568 19.2648 7.63502 19.206 7.95941C19.1472 8.28381 19.1869 8.61838 19.32 8.92V9C19.4468 9.29577 19.6572 9.54802 19.9255 9.72569C20.1938 9.90337 20.5082 9.99872 20.83 10H21C21.5304 10 22.0391 10.2107 22.4142 10.5858C22.7893 10.9609 23 11.4696 23 12C23 12.5304 22.7893 13.0391 22.4142 13.4142C22.0391 13.7893 21.5304 14 21 14H20.91C20.5882 14.0013 20.2738 14.0966 20.0055 14.2743C19.7372 14.452 19.5268 14.7042 19.4 15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );

  useEffect(() => {
    // Initialize the app
    fetch('/api/init')
      .then(response => response.json())
      .then(data => {
        setDocuments(data.documents);
        setThreadId(data.threadId);
      })
      .catch(error => console.error('Error initializing app:', error));
  }, []);

  useEffect(() => {
    // Scroll to bottom of chat when history changes
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [message]);

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    // Add user message to chat
    setChatHistory(prev => [...prev, { role: 'user', content: message }]);
    setLoading(true);
    
    // Store the message before clearing it
    const currentMessage = message;
    
    // Clear the input immediately after sending
    setMessage('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    
    try {
      // Add timeout parameter if enabled
      const queryWithTimeout = timeout > 0 ? `${currentMessage} timeout=${timeout}` : currentMessage;
      
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: queryWithTimeout })
      });
      
      const data = await response.json();
      
      // Add assistant response to chat
      setChatHistory(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      console.error('Error sending message:', error);
      setChatHistory(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, there was an error processing your request.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = async () => {
    try {
      await fetch('/api/chat/clear', { method: 'POST' });
      setChatHistory([]);
    } catch (error) {
      console.error('Error clearing chat:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    
    setLoading(true);
    
    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Refresh document list
        const docsResponse = await fetch('/api/documents');
        const docsData = await docsResponse.json();
        setDocuments(docsData.documents);
        
        // Switch to chat tab
        setActiveTab('chat');
        
        // Add system message
        setChatHistory(prev => [...prev, { 
          role: 'assistant', 
          content: `I've processed your document "${file.name}". You can now ask questions about it.` 
        }]);
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error uploading file');
    } finally {
      setLoading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteDocument = async (document) => {
    if (!window.confirm(`Are you sure you want to delete ${document}?`)) return;
    
    try {
      const response = await fetch('/api/documents/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Refresh document list
        const docsResponse = await fetch('/api/documents');
        const docsData = await docsResponse.json();
        setDocuments(docsData.documents);
        
        // Add system message
        setChatHistory(prev => [...prev, { 
          role: 'assistant', 
          content: `Document "${document}" has been deleted.` 
        }]);
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error deleting document:', error);
      alert('Error deleting document');
    }
  };

  // Function to render message content with improved markdown support
  const renderMessageContent = (content) => {
    // Simple markdown rendering for code blocks
    if (content.includes('```')) {
      const parts = content.split('```');
      return (
        <>
          {parts.map((part, index) => {
            if (index % 2 === 0) {
              return <span key={index}>{part}</span>;
            } else {
              // Extract language if specified
              const firstLineBreak = part.indexOf('\n');
              let language = '';
              let code = part;
              
              if (firstLineBreak > 0) {
                language = part.substring(0, firstLineBreak).trim();
                code = part.substring(firstLineBreak + 1);
              }
              
              return (
                <pre key={index} className={language ? `language-${language}` : ''}>
                  {language && <div className="code-language">{language}</div>}
                  <code>{code}</code>
                </pre>
              );
            }
          })}
        </>
      );
    }
    
    // Handle line breaks
    return content.split('\n').map((line, i) => (
      <React.Fragment key={i}>
        {line}
        {i < content.split('\n').length - 1 && <br />}
      </React.Fragment>
    ));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Add this to the chat input container
  const renderSettings = () => (
    <div className={`settings-panel ${showSettings ? 'show' : ''}`}>
      <div className="settings-header">
        <h3>Settings</h3>
        <button onClick={() => setShowSettings(false)}>×</button>
      </div>
      <div className="settings-content">
        <div className="setting-item">
          <label htmlFor="timeout">Response Timeout (seconds):</label>
          <div className="setting-control">
            <input
              type="range"
              id="timeout"
              min="0"
              max="120"
              step="5"
              value={timeout}
              onChange={(e) => setTimeout(parseInt(e.target.value))}
            />
            <span className="setting-value">{timeout === 0 ? 'No limit' : `${timeout}s`}</span>
          </div>
          <p className="setting-description">
            {timeout === 0 
              ? 'No timeout limit - responses may take longer for complex queries.' 
              : `If response takes longer than ${timeout} seconds, processing will stop.`}
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="app">
      {/* Mobile header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <i className="brain-icon"><BrainIcon /></i>
            <h1>Genie</h1>
          </div>
          <div className="tabs">
            <button 
              className={activeTab === 'chat' ? 'active' : ''} 
              onClick={() => setActiveTab('chat')}
            >
              Chat
            </button>
            <button 
              className={activeTab === 'documents' ? 'active' : ''} 
              onClick={() => setActiveTab('documents')}
            >
              Documents
            </button>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={handleClearChat}>
            <PlusIcon /> New chat
          </button>
        </div>
        <div className="sidebar-tabs">
          <button 
            className={activeTab === 'chat' ? 'active' : ''} 
            onClick={() => setActiveTab('chat')}
          >
            <FileIcon /> Chat
          </button>
          <button 
            className={activeTab === 'documents' ? 'active' : ''} 
            onClick={() => setActiveTab('documents')}
          >
            <UploadIcon /> Documents
          </button>
        </div>
        <div className="sidebar-footer">
          <div className="logo">
            <i className="brain-icon"><BrainIcon size={20} /></i>
            <span>Genie</span>
          </div>
        </div>
      </div>

      {/* Main content */}
      <main className="main">
        {activeTab === 'chat' ? (
          <div className="chat-container">
            <div className="chat-messages" ref={chatContainerRef}>
              {chatHistory.length === 0 ? (
                <div className="welcome-message">
                  <h2>Genie - AI Database Assistant</h2>
                  <p>Retrieval Augmented Generation (RAG) tool for extracting insights from your documents.</p>
                </div>
              ) : (
                <>
                  <div className="chat-header">
                    <h2>Genie - AI Database Assistant</h2>
                  </div>
                  {chatHistory.map((msg, index) => (
                    <div key={index} className={`message ${msg.role}`}>
                      <div className="message-content">
                        {renderMessageContent(msg.content)}
                      </div>
                    </div>
                  ))}
                </>
              )}
              {loading && (
                <div className="message assistant">
                  <div className="message-content loading">Thinking</div>
                </div>
              )}
            </div>
            <div className="chat-input-container">
              <div className="chat-input">
                <div className="chat-input-field">
                  <textarea
                    ref={textareaRef}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask a question about your documents..."
                    disabled={loading}
                  />
                  <button 
                    className="send-btn" 
                    onClick={handleSendMessage} 
                    disabled={loading || !message.trim()}
                    title="Send message"
                  >
                    <SendIcon />
                  </button>
                </div>
                <div className="chat-input-actions">
                  <button 
                    className="settings-btn" 
                    onClick={() => setShowSettings(!showSettings)}
                    title="Settings"
                  >
                    <SettingsIcon /> Settings
                  </button>
                  <button 
                    className="clear-btn" 
                    onClick={handleClearChat} 
                    disabled={loading || chatHistory.length === 0}
                    title="Clear conversation"
                  >
                    <TrashIcon /> Clear conversation
                  </button>
                </div>
                <div className="chat-input-hint">
                  Press Enter to send, Shift+Enter for a new line
                </div>
                {renderSettings()}
              </div>
            </div>
          </div>
        ) : (
          <div className="documents-container">
            <div className="upload-section">
              <h2>Upload Documents</h2>
              <p>Upload PDF, Excel, or CSV files (up to 10GB)</p>
              <div className="file-upload" onClick={() => fileInputRef.current.click()}>
                <input 
                  type="file" 
                  ref={fileInputRef}
                  onChange={handleFileUpload} 
                  accept=".pdf,.xlsx,.xls,.csv"
                />
                <div className="file-upload-icon">
                  <UploadIcon />
                </div>
                <div className="file-upload-text">
                  <p>Drag and drop files here or <strong>click to browse</strong></p>
                  <p>Supported formats: PDF, Excel, CSV</p>
                </div>
              </div>
            </div>
            <div className="documents-list">
              <h2>Your Documents</h2>
              {documents.length === 0 ? (
                <p>No documents uploaded yet.</p>
              ) : (
                <ul>
                  {documents.map((doc, index) => (
                    <li key={index}>
                      <div className="document-info">
                        <div className="document-icon">
                          <FileIcon />
                        </div>
                        <span className="document-name">{doc}</span>
                      </div>
                      <button onClick={() => handleDeleteDocument(doc)}>Delete</button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>Genie - Powered by LangChain, LangGraph, and OpenAI</p>
      </footer>
    </div>
  );
}

export default App;