import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Paperclip } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm' // Import GFM (GitHub Flavored Markdown)

interface Message {
  id: number
  text: string
  sender: 'user' | 'bot'
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [hasInteracted, setHasInteracted] = useState(false)
  const [showHeader, setShowHeader] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const lastScrollTop = useRef(0)
  const isScrollingRef = useRef(false)

  const [overlayHeight, setOverlayHeight] = useState(150) // Default height in pixels

  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current && !isScrollingRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [])

  useEffect(() => {
    if (messages.length > 0 && messages[messages.length - 1].sender === 'bot') {
      scrollToBottom()
    }
  }, [messages, scrollToBottom])
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      const newHeight = Math.min(textareaRef.current.scrollHeight, 150) // Max height of 150px
      textareaRef.current.style.height = `${newHeight}px`
    }
  }, [input])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      setHasInteracted(true);
      const userMessage: Message = { id: Date.now(), text: input, sender: 'user' };
      setMessages(prevMessages => [...prevMessages, userMessage]);
      setInput('');
      setIsStreaming(true);

      // Show header only after user hits submit for the first time
      setShowHeader(true); 

      try {
        const response = await fetch('http://localhost:8000/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: input }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (reader) {
          let botResponse = '';
          while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            botResponse += chunk;
            setMessages(prevMessages => {
              const lastMessage = prevMessages[prevMessages.length - 1];
              if (lastMessage && lastMessage.sender === 'bot') {
                return [
                  ...prevMessages.slice(0, -1),
                  { ...lastMessage, text: botResponse },
                ];
              } else {
                return [
                  ...prevMessages,
                  { id: Date.now(), text: botResponse, sender: 'bot' },
                ];
              }
            });
          }
        }
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setIsStreaming(false);
      }
    }
  };

  const handleAttachment = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      console.log('File selected:', file.name)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  const handleScroll = useCallback(() => {
    const container = chatContainerRef.current
    if (container) {
      const { scrollTop, scrollHeight, clientHeight } = container
      const isAtBottom = scrollHeight - scrollTop === clientHeight
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100

      if (isAtBottom) {
        setShowHeader(true)
      } else if (scrollTop > lastScrollTop.current && !isNearBottom) {
        setShowHeader(false)
      } else if (scrollTop < lastScrollTop.current) {
        setShowHeader(true)
      }

      lastScrollTop.current = scrollTop
    }
  }, [])

  // Call this function whenever you want to change the overlay height dynamically
  const updateOverlayHeight = (newHeight: number) => {
    setOverlayHeight(newHeight)
  }

  const customComponents = {
    code({ node, inline, className, children, ...props }: { node: any, inline: boolean, className: string, children: any }) {
      const match = /language-(\w+)/.exec(className || '')
      return !inline ? (
        <div className=" bg-gray-800 m-0 rounded-md max-w-xl">
          <div className="text-gray-200 bg-gray-700 px-4 py-2 text-xs font-sans m-0 rounded-t-md">
            <span>{match ? match[1] : 'code'}</span>
          </div>
          <pre className="bg-gray-800 rounded-b-md max-w-full p-4 m-0 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800">
            <code className="bg-gray-800 text-white px-1 max-w-md py-0.5 text-sm font-mono" {...props}>
              {children}
            </code>
          </pre>
        </div>
      ) : (
        <code className="!whitespace-pre text-white text-sm font-mono" {...props}>
          {children}
        </code>
      )
    },
    a({ node, href, children, ...props }: { node: any, href: string, children: any }) {
      const isCodeBlock = node.parent?.type === 'code'
      return isCodeBlock ? (
        <span className="text-blue-300" {...props}>{children}</span>
      ) : (
        <a href={href} className="text-blue-500 hover:underline" target="_blank" rel="noopener noreferrer" {...props}>
          {children}
        </a>
      )
    },
    p({ node, children, ...props }: { node: any, children: any }) {
      const isWithinCodeBlock = node.parent?.type === 'code'
      return isWithinCodeBlock ? (
        <span className="block mb-2" {...props}>{children}</span>
      ) : (
        <p {...props}>{children}</p>
      )
    },
    pre({ node, children, ...props }: { node: any, children: any }) {
      return (
        <div className="m-0 min-w-full" {...props}>
          {children}
        </div>
      )
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100 text-gray-800">
      <header 
        className={`z-30 fixed top-0 left-0 right-0 bg-gradient-to-b from-gray-300 to-transparent p-4 text-center transition-all duration-300 ${
          showHeader && hasInteracted ? 'translate-y-0' : '-translate-y-full'
        }`}
      >
        <h1 className="text-2xl font-bold">Gracii</h1>
      </header>
      <main className={`flex-1 overflow-hidden flex flex-col transition-all duration-300 ${showHeader ? 'pt-16' : 'pt-0'}`}>
        <div 
          ref={chatContainerRef}
          className="flex-1 overflow-auto scrollbar-hide scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 relative"
          onScroll={handleScroll}
        >
          <div className="fixed top-0 left-0 right-0 bottom-0 pointer-events-none z-20">
            <div 
              className="bg-gradient-to-b from-gray-100 via-transparent to-transparent"
              style={{ height: `${overlayHeight}px` }} // Use the overlayHeight state here
            ></div>
          </div>
          <div className="max-w-2xl mx-auto pb-24 relative z-10">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex items-start mb-4 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex items-start space-x-2 ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  {message.sender === 'bot' && (
                    <div className="p-2 rounded-full bg-gray-300">
                      <div className="w-6 h-6 bg-gray-500 rounded-full flex items-center justify-center">
                        <span className="text-xs font-bold text-white">AI</span>
                      </div>
                    </div>
                  )}
                  <div className={`p-3 rounded-lg ${message.sender === 'user' ? 'bg-gray-300 max-w-md shadow' : 'bg-gray-100 max-w-full'} `}>
                    <ReactMarkdown
                      className="prose max-w-full"
                      remarkPlugins={[remarkGfm]}
                      components={customComponents}
                    >
                      {message.text}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>
        <div className={`bg-gray-100 transition-all duration-300 ease-in-out ${hasInteracted ? '' : 'mb-72'} relative z-30`}>
          <form onSubmit={handleSubmit} className="max-w-2xl mx-auto">
            <div className="relative flex items-center bg-white rounded-3xl shadow-md">
              <button 
                type="button"
                onClick={handleAttachment}
                className="p-3 text-gray-500 hover:text-gray-700 focus:outline-none"
              >
                <Paperclip className="w-5 h-5" />
              </button>
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="flex-grow p-3 bg-transparent text-gray-800 focus:outline-none resize-none"
                disabled={isStreaming}
                rows={1}
                style={{ maxHeight: '150px', overflowY: 'auto' }}
              />
              <button 
                type="submit" 
                className="p-3 text-gray-500 hover:text-gray-700 focus:outline-none"
                disabled={isStreaming}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </form>
          <div>
            <span className="flex justify-center text-gray-500 text-xs p-2">Gracii can make mistakes. Check important info.</span>
          </div>
        </div>
      </main>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  )
}

export default App;
