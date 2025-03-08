import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState(null);
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
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
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
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
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