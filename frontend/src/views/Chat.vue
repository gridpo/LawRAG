<template>
  <div class="dashboard-container">
    
    <div class="sidebar">
      <div class="sidebar-top">
        <div class="logo-box" title="LawRAG">
          <span class="logo-icon">⚖️</span>
        </div>
        <div class="nav-item" :class="{ active: activeMenu === 'chat' }" @click="switchMenu('chat')" title="对话中心">
          <el-icon :size="24"><ChatDotRound /></el-icon>
        </div>
        <div class="nav-item" :class="{ active: activeMenu === 'kb' }" @click="switchMenu('kb')" title="知识库管理">
          <el-icon :size="24"><Files /></el-icon>
        </div>
        <div class="nav-item" :class="{ active: activeMenu === 'profile' }" @click="switchMenu('profile')" title="个人信息">
          <el-icon :size="24"><User /></el-icon>
        </div>
      </div>
      <div class="sidebar-bottom">
        <el-dropdown trigger="click" @command="handleCommand">
          <el-avatar :size="40" class="user-avatar">{{ username.charAt(0).toUpperCase() }}</el-avatar>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout" style="color: red;">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="session-manager" v-show="activeMenu === 'chat'">
      <div class="session-header">
        <h3>我的会话</h3>
        <el-button type="primary" class="new-chat-btn" :icon="Plus" @click="createNewSession">新建对话</el-button>
      </div>
      <div class="session-search">
        <el-input v-model="searchQuery" placeholder="搜索历史会话..." :prefix-icon="Search" clearable />
      </div>
      <div class="session-list">
        <div 
          v-for="session in filteredSessions" 
          :key="session.id" 
          class="session-item"
          :class="{ active: currentSessionId === session.id }"
          @click="selectSession(session.id)"
        >
          <el-icon class="session-icon"><ChatLineSquare /></el-icon>
          <div class="session-info">
            <div class="session-title">{{ session.title }}</div>
            <div class="session-time">{{ session.time }}</div>
          </div>
          <el-icon class="delete-icon" @click.stop="deleteSession(session.id)"><Delete /></el-icon>
        </div>
      </div>
    </div>

    <div class="main-content">
      
      <div class="chat-area" v-if="activeMenu === 'chat'">
        <div class="chat-header">
          <h2 v-if="currentSessionId">{{ currentSessionTitle }}</h2>
          <h2 v-else>新对话</h2>
        </div>

        <div class="chat-messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="empty-chat">
            <el-icon :size="60" color="#c0c4cc"><Microphone /></el-icon>
            <p>我是您的专属法律助手，请描述您的法律问题。</p>
          </div>

          <div v-for="(msg, index) in messages" :key="index" class="message-wrapper" :class="msg.role === 'user' ? 'is-user' : 'is-ai'">
            <el-avatar :size="36" class="msg-avatar" :style="{ background: msg.role === 'user' ? '#007bff' : '#28a745' }">
              {{ msg.role === 'user' ? 'U' : 'AI' }}
            </el-avatar>
            
            <div class="message-content-group">
              <div class="message-bubble">
                <div v-if="msg.role === 'assistant'" class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
                <div v-else class="plain-text">{{ msg.content }}</div>
              </div>
              
              <div v-if="msg.role === 'assistant' && msg.sources && msg.sources.length > 0" class="source-btn-wrap">
                <el-button size="small" round @click="openSourceDrawer(msg.sources)">
                  <el-icon><Reading /></el-icon> 查看参考依据
                </el-button>
              </div>
            </div>

          </div>
          
          <div v-if="isGenerating" class="message-wrapper is-ai">
             <el-avatar :size="36" class="msg-avatar" style="background: #28a745;">AI</el-avatar>
             <div class="message-content-group">
               <div class="message-bubble typing-indicator">
                  <span class="dot"></span><span class="dot"></span><span class="dot"></span>
               </div>
             </div>
          </div>
        </div>

        <div class="chat-input-area">
          <div class="input-container">
            <el-input v-model="inputText" type="textarea" :rows="3" resize="none" placeholder="输入您的法律问题，按 Enter 发送..." @keydown.enter.prevent="handleEnter" />
            <el-button type="primary" class="send-btn" :disabled="!inputText.trim() || isGenerating" @click="sendMessage">
              <el-icon><Position /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <div class="kb-area" v-if="activeMenu === 'kb'">
        <div class="kb-header">
          <h2>📚 法律知识库</h2>
          <p>上传法律条文或案例 PDF，大模型将自动学习并作为回答的参考依据。</p>
        </div>
        
        <div class="kb-content">
          <el-upload
            class="kb-upload"
            drag
            action="/api/v1/documents/upload"
            :headers="uploadHeaders"
            accept=".pdf,.txt"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :show-file-list="false"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip text-center">支持 PDF、TXT 格式文件。上传后系统在后台进行向量化切片。</div>
            </template>
          </el-upload>

          <div class="doc-list-container">
            <div class="list-header">
              <h3>已学习文档 ({{ documentList.length }})</h3>
              <el-button type="primary" text :icon="Refresh" @click="fetchDocuments">刷新状态</el-button>
            </div>
            
            <el-table :data="documentList" style="width: 100%" v-loading="loadingDocs">
              <el-table-column prop="filename" label="文档名称" min-width="200">
                <template #default="scope">
                  <el-icon style="margin-right: 8px; color: #6c757d;"><Document /></el-icon>
                  <strong>{{ scope.row.filename }}</strong>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="上传时间" width="180" />
              <el-table-column prop="status" label="学习状态" width="120">
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'completed'" type="success" effect="light">已掌握</el-tag>
                  <el-tag v-else-if="scope.row.status === 'processing'" type="warning" effect="light" class="pulsing">学习中...</el-tag>
                  <el-tag v-else type="danger" effect="light">解析失败</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" align="center">
                <template #default="scope">
                  <el-button type="danger" :icon="Delete" circle plain @click="deleteDoc(scope.row.id)" />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>

      <div class="profile-area" v-if="activeMenu === 'profile'">
        <div class="profile-header">
          <h2>👤 个人中心</h2>
          <p>管理您的账户信息与系统设置。</p>
        </div>
        
        <div class="profile-content">
          <div class="profile-grid">
            <div class="profile-left">
              <el-card class="user-card" shadow="hover">
                <div class="user-profile-layout">
                  <el-avatar :size="80" class="large-avatar">{{ username.charAt(0).toUpperCase() }}</el-avatar>
                  <div class="user-info">
                    <h3>{{ username }}</h3>
                    <p class="user-role">尊贵的 LawRAG 专属用户</p>
                    <el-button type="danger" plain @click="handleCommand('logout')">退出登录</el-button>
                  </div>
                </div>
              </el-card>

              <el-card class="stats-card" shadow="hover" style="margin-top: 20px;">
                <template #header>
                  <div class="card-header">
                    <span>📊 使用统计</span>
                  </div>
                </template>
                <el-descriptions border :column="1">
                  <el-descriptions-item label="历史对话数"><strong>{{ sessions.length }}</strong> 次</el-descriptions-item>
                  <el-descriptions-item label="已掌握文档"><strong>{{ documentList.length }}</strong> 份</el-descriptions-item>
                  <el-descriptions-item label="账号状态"><el-tag type="success" size="small">运行正常</el-tag></el-descriptions-item>
                  <el-descriptions-item label="系统版本"><el-tag type="info" size="small">v1.0.0 (Pro)</el-tag></el-descriptions-item>
                </el-descriptions>
              </el-card>
            </div>

            <div class="profile-right">
              <el-card class="info-card" shadow="hover">
                <template #header>
                  <div class="card-header"><el-icon><Bell /></el-icon> 系统更新公告</div>
                </template>
                <el-timeline>
                  <el-timeline-item timestamp="刚刚" type="primary" hollow>
                    <strong>LawRAG v1.0 旗舰版正式上线！</strong><br/>
                    <span style="color: #6c757d; font-size: 13px;">支持本地法律知识库拖拽解析，提供精准溯源的法律问答。</span>
                  </el-timeline-item>
                  <el-timeline-item timestamp="昨日" type="success" hollow>
                    <strong>流式对话引擎升级</strong><br/>
                    <span style="color: #6c757d; font-size: 13px;">接入最新 SSE 技术，体验如丝般顺滑的打字机输出效果。</span>
                  </el-timeline-item>
                  <el-timeline-item timestamp="本周" color="#e4e7ed">
                    <strong>安全架构部署完成</strong><br/>
                    <span style="color: #6c757d; font-size: 13px;">全站启用 HTTPS 加密传输，保障您的对话与文档隐私。</span>
                  </el-timeline-item>
                </el-timeline>
              </el-card>

              <el-card class="info-card" shadow="hover" style="margin-top: 20px;">
                <template #header>
                  <div class="card-header"><el-icon><Notebook /></el-icon> 快速上手指南</div>
                </template>
                <div class="guide-content">
                  <p><strong>1. 智能问答：</strong> 在左侧导航栏点击「对话中心」，直接输入您的法律问题，系统将基于现有法律库作答。</p>
                  <p><strong>2. 精准溯源：</strong> AI 回答完毕后，点击回答气泡下方的「查看参考依据」按钮，即可核对法律原文出处。</p>
                  <p><strong>3. 培养专属 AI：</strong> 遇到超纲问题？点击「知识库管理」，上传您自己的 PDF/TXT 文件。AI 学习完成后，将立刻为您解答新知识！</p>
                </div>
              </el-card>
            </div>
          </div>
        </div>
      </div>

    </div>

    <el-drawer v-model="drawerVisible" title="📚 AI 参考的法律依据" size="400px">
      <div class="source-list">
        <el-card v-for="(source, index) in currentSources" :key="index" class="source-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span class="source-filename">{{ formatSourceName(source) }}</span>
            </div>
          </template>
          <div class="source-content">{{ source.content }}...</div>
        </el-card>
      </div>
    </el-drawer>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../api/request'
// ⚠️ 注意：这里补充了 Bell 和 Notebook 两个图标
import { ChatDotRound, User, Plus, Search, ChatLineSquare, Delete, Position, Microphone, Files, UploadFilled, Document, Refresh, Reading, Bell, Notebook } from '@element-plus/icons-vue'

import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const router = useRouter()
const userStore = useUserStore()
const username = computed(() => userStore.username || 'User')

// 菜单与抽屉状态
const activeMenu = ref('chat')
const drawerVisible = ref(false)
const currentSources = ref([])

// 万能文件名提取器
const formatSourceName = (src) => {
  if (!src) return '参考文档'
  // 1. 兼容各种后端的返回格式（涵盖了 metadata 嵌套的情况）
  const path = src.metadata?.source || src.source || src.file_name || src.filename || ''
  
  if (!path) return '参考文档'
  
  // 2. 砍掉冗长的服务器绝对路径，只保留文件名
  let filename = path.split(/[/\\]/).pop()
  
  // 3. 砍掉我们为了防重名加的 "sys_" 前缀
  filename = filename.replace(/^sys_/, '')
  
  return filename
}

const switchMenu = (menu) => {
  activeMenu.value = menu
  if (menu === 'kb') fetchDocuments()
}

const openSourceDrawer = (sources) => {
  currentSources.value = sources
  drawerVisible.value = true
}

// ================== 聊天模块逻辑 ==================
const sessions = ref([])
const searchQuery = ref('')
const currentSessionId = ref(null)
const messages = ref([])
const inputText = ref('')
const isGenerating = ref(false)
const messagesContainer = ref(null)

const md = new MarkdownIt({
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try { return hljs.highlight(str, { language: lang }).value } catch (__) {}
    }
    return ''
  }
})
const renderMarkdown = (text) => md.render(text || '')

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

onMounted(async () => {
  try {
    const res = await request.get('/chat/sessions')
    sessions.value = res
  } catch (error) {}
})

const filteredSessions = computed(() => {
  return sessions.value.filter(s => s.title.includes(searchQuery.value))
})

const currentSessionTitle = computed(() => {
  const s = sessions.value.find(s => s.id === currentSessionId.value)
  return s ? s.title : '新对话'
})

const selectSession = async (id) => {
  currentSessionId.value = id
  messages.value = [] 
  try {
    const res = await request.get(`/chat/sessions/${id}/messages`)
    messages.value = res
    scrollToBottom()
  } catch (error) {
    ElMessage.error('获取历史消息失败')
  }
}

const deleteSession = async (id) => {
  try {
    await request.delete(`/chat/sessions/${id}`)
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (currentSessionId.value === id) createNewSession()
    ElMessage.success('会话已删除')
  } catch (error) {}
}

const createNewSession = () => {
  currentSessionId.value = null
  messages.value = []
}

const handleEnter = (e) => {
  if (!e.shiftKey) sendMessage()
  else inputText.value += '\n'
}

const sendMessage = async () => {
  const query = inputText.value.trim()
  if (!query || isGenerating.value) return

  messages.value.push({ role: 'user', content: query })
  inputText.value = ''
  isGenerating.value = true
  scrollToBottom()

  // 占位
  messages.value.push({ role: 'assistant', content: '', sources: [] })
  const aiMessageIndex = messages.value.length - 1

  try {
    const token = localStorage.getItem('token')
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ query: query, session_id: currentSessionId.value })
    })

    if (!response.ok) throw new Error('网络请求失败')

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.replace('data: ', '')
          if (dataStr === '[DONE]') break
          try {
            const dataObj = JSON.parse(dataStr)
            if (dataObj.type === 'meta') {
              // 捕获后端的来源信息
              if (dataObj.sources) {
                messages.value[aiMessageIndex].sources = dataObj.sources
              }
              if (!currentSessionId.value && dataObj.session_id) {
                currentSessionId.value = dataObj.session_id
                sessions.value.unshift({ id: dataObj.session_id, title: query.substring(0, 10), time: '刚刚' })
              }
            } else if (dataObj.type === 'content') {
              messages.value[aiMessageIndex].content += dataObj.data
              scrollToBottom()
            }
          } catch (e) {}
        }
      }
    }
  } catch (error) {
    messages.value[aiMessageIndex].content = '抱歉，系统响应失败，请重试。'
  } finally {
    isGenerating.value = false
    scrollToBottom()
  }
}

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}

// ================== 知识库模块逻辑 ==================
const documentList = ref([])
const loadingDocs = ref(false)

const uploadHeaders = computed(() => {
  return { Authorization: `Bearer ${localStorage.getItem('token')}` }
})

const fetchDocuments = async () => {
  loadingDocs.value = true
  try {
    const res = await request.get('/documents/')
    documentList.value = res
  } catch (error) {} finally {
    loadingDocs.value = false
  }
}

const deleteDoc = (id) => {
  ElMessageBox.confirm('这会同时删除后台的向量数据，确定删除吗？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await request.delete(`/documents/${id}`)
      ElMessage.success('删除成功')
      fetchDocuments()
    } catch (error) {}
  }).catch(() => {})
}

const handleUploadSuccess = (response) => {
  ElMessage.success(response.message || '上传成功，后台开始解析')
  fetchDocuments()
}

const handleUploadError = () => {
  ElMessage.error('上传失败，请检查文件类型或网络')
}
</script>

<style scoped>
/* =========== 基础容器与导航 =========== */
.dashboard-container { display: flex; height: 100vh; width: 100vw; background-color: #f0f2f5; padding: 20px; box-sizing: border-box; gap: 20px; }
.sidebar { width: 80px; background-color: #ffffff; border-radius: 20px; display: flex; flex-direction: column; align-items: center; justify-content: space-between; padding: 30px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); flex-shrink: 0; }
.sidebar-top { display: flex; flex-direction: column; align-items: center; width: 100%; }
.logo-box { width: 42px; height: 42px; background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); border-radius: 12px; display: flex; justify-content: center; align-items: center; margin-bottom: 40px; box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3); cursor: pointer; flex-shrink: 0;}
.logo-icon { font-size: 22px; }
.nav-item { width: 50px; height: 50px; border-radius: 12px; display: flex; justify-content: center; align-items: center; margin-bottom: 15px; color: #6c757d; cursor: pointer; transition: all 0.3s; }
.nav-item:hover { background-color: #f8f9fa; color: #007bff; }
.nav-item.active { background-color: #e6f2ff; color: #007bff; }
.user-avatar { cursor: pointer; background-color: #007bff; }
.session-manager { width: 300px; background-color: #ffffff; border-radius: 20px; display: flex; flex-direction: column; box-shadow: 0 4px 12px rgba(0,0,0,0.05); flex-shrink: 0; }
.session-header { padding: 25px 20px 15px; display: flex; justify-content: space-between; align-items: center; }
.session-header h3 { margin: 0; font-size: 18px; color: #343a40; }
.new-chat-btn { border-radius: 8px; }
.session-search { padding: 0 20px 15px; }
:deep(.session-search .el-input__wrapper) { border-radius: 8px; background-color: #f8f9fa; box-shadow: none; }
.session-list { flex: 1; overflow-y: auto; padding: 0 10px 20px; }
.session-item { display: flex; align-items: center; padding: 15px; border-radius: 12px; margin-bottom: 8px; cursor: pointer; transition: all 0.2s; position: relative; }
.session-item:hover { background-color: #f8f9fa; }
.session-item.active { background-color: #e6f2ff; }
.session-icon { font-size: 20px; color: #6c757d; margin-right: 12px; }
.session-item.active .session-icon { color: #007bff; }
.session-info { flex: 1; overflow: hidden; }
.session-title { font-size: 14px; color: #343a40; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.session-time { font-size: 12px; color: #adb5bd; }
.delete-icon { display: none; color: #dc3545; padding: 5px; }
.session-item:hover .delete-icon { display: block; }
.main-content { flex: 1; background-color: #ffffff; border-radius: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); display: flex; flex-direction: column; overflow: hidden; min-width: 0; }

/* =========== 聊天区域 =========== */
.chat-area { display: flex; flex-direction: column; height: 100%; }
.chat-header { padding: 20px 30px; border-bottom: 1px solid #f0f2f5; display: flex; align-items: center; }
.chat-header h2 { margin: 0; font-size: 18px; color: #343a40; font-weight: 600; }
.chat-messages { flex: 1; padding: 30px; overflow-y: auto; display: flex; flex-direction: column; background-color: #fafbfc; }
.empty-chat { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #6c757d; }
.empty-chat p { margin-top: 20px; font-size: 16px; }
.message-wrapper { display: flex; margin-bottom: 30px; max-width: 85%; }
.message-wrapper.is-user { align-self: flex-end; flex-direction: row-reverse; }
.message-wrapper.is-ai { align-self: flex-start; }
.msg-avatar { flex-shrink: 0; font-size: 14px; }
.is-user .msg-avatar { margin-left: 15px; }
.is-ai .msg-avatar { margin-right: 15px; }

/* =========== 溯源与气泡布局 =========== */
.message-content-group {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.message-bubble { padding: 15px 20px; border-radius: 16px; font-size: 15px; line-height: 1.6; color: #343a40; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
.is-user .message-bubble { background-color: #007bff; color: #ffffff; border-top-right-radius: 4px; }
.is-ai .message-bubble { background-color: #ffffff; border-top-left-radius: 4px; }
.plain-text { white-space: pre-wrap; }

.source-btn-wrap {
  margin-top: 8px;
  margin-left: 5px;
}
.source-btn-wrap .el-button {
  background-color: transparent;
  color: #6c757d;
  border-color: #e2e6ea;
}
.source-btn-wrap .el-button:hover {
  color: #007bff;
  border-color: #007bff;
  background-color: #f8f9fa;
}

/* 抽屉内卡片样式 */
.source-card {
  margin-bottom: 15px;
  border-radius: 12px;
}
.card-header {
  display: flex;
  align-items: center;
  color: #343a40;
  font-weight: bold;
}
.source-filename {
  margin-left: 8px;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.source-content {
  font-size: 13px;
  color: #6c757d;
  line-height: 1.6;
}

/* =========== 输入区 =========== */
.chat-input-area {
  padding: 20px 30px; 
  background-color: #ffffff; 
  border-top: 1px solid #f0f2f5; 
}

.input-container { 
  position: relative; 
  background-color: #f8f9fa; 
  border-radius: 16px; 
  padding: 10px 15px; 
  border: 1px solid #e0e0e0; 
  transition: all 0.3s; 
}

.input-container:focus-within { 
  border-color: #007bff; 
  box-shadow: 0 0 0 2px rgba(0,123,255,0.1); 
}

:deep(.input-container .el-textarea__inner) { 
  background-color: transparent; 
  border: none; 
  box-shadow: none; 
  padding-right: 50px; 
  color: #343a40; 
  font-size: 15px; 
}

.send-btn { 
  position: absolute; 
  right: 15px; 
  bottom: 15px; 
  border-radius: 12px; 
  width: 40px; 
  height: 40px; 
  padding: 0; 
}

.typing-indicator .dot { 
  display: inline-block; 
  width: 6px; 
  height: 6px; 
  background-color: #adb5bd; 
  border-radius: 50%; 
  margin: 0 2px; 
  animation: bounce 1.4s infinite ease-in-out both; 
}

.typing-indicator .dot:nth-child(1) { 
  animation-delay: -0.32s; 
}

.typing-indicator .dot:nth-child(2) { 
  animation-delay: -0.16s; 
}

@keyframes bounce { 
  0%, 80%, 100% { 
    transform: scale(0); 
  } 40% { 
    transform: scale(1); 
  } 
}

:deep(.markdown-body) { 
  font-family: inherit; 
}

:deep(.markdown-body p) { 
  margin-top: 0; 
  margin-bottom: 10px; 
}

:deep(.markdown-body p:last-child) { 
  margin-bottom: 0; 
}

:deep(.markdown-body pre) { 
  background-color: #f6f8fa; 
  padding: 15px; 
  border-radius: 8px; 
  overflow-x: auto; 
}

/* =========== 知识库管理区 =========== */
.kb-area { 
  display: flex; 
  flex-direction: column; 
  height: 100%; 
  background-color: #fafbfc; 
}

.kb-header { 
  padding: 30px; 
  background-color: #ffffff; 
  border-bottom: 1px solid #f0f2f5; 
}

.kb-header h2 { 
  margin: 0 0 10px 0; 
  font-size: 22px; 
  color: #343a40; 
}

.kb-header p { 
  margin: 0; 
  color: #6c757d; 
  font-size: 14px; 
}

.kb-content { 
  flex: 1; 
  padding: 30px; 
  overflow-y: auto; 
  display: flex; 
  flex-direction: column; 
  gap: 30px; 
}

.kb-upload { 
  width: 100%; 
}

:deep(.kb-upload .el-upload-dragger) { 
  background-color: #ffffff; 
  border-radius: 16px; 
  border: 2px dashed #dcdfe6; 
  transition: all 0.3s; 
}

:deep(.kb-upload .el-upload-dragger:hover) { 
  border-color: #007bff; 
  background-color: #f8f9fa; 
}

.doc-list-container { 
  background-color: #ffffff; 
  border-radius: 16px; 
  padding: 20px; 
  box-shadow: 0 2px 12px rgba(0,0,0,0.03); 
}

.list-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 20px; 
}

.list-header h3 { 
  margin: 0; 
  font-size: 16px; 
  color: #343a40; 
}

.text-center { 
  text-align: center; 
}

.pulsing { 
  animation: pulse 1.5s infinite; 
}

@keyframes pulse { 
  0% {
     opacity: 1; 
     } 
     50% {
       opacity: 0.6; 
       } 
       100% 
       { opacity: 1; } 
}

/* =========== 个人信息区 (优化版) =========== */
.profile-area { display: flex; flex-direction: column; height: 100%; background-color: #fafbfc; }
.profile-header { padding: 30px; background-color: #ffffff; border-bottom: 1px solid #f0f2f5; }
.profile-header h2 { margin: 0 0 10px 0; font-size: 22px; color: #343a40; }
.profile-header p { margin: 0; color: #6c757d; font-size: 14px; }

.profile-content { flex: 1; padding: 40px; overflow-y: auto; width: 100%; box-sizing: border-box; }
.profile-grid { display: flex; gap: 30px; max-width: 1100px; margin: 0 auto; align-items: flex-start; flex-wrap: wrap; }

.profile-left { flex: 1; min-width: 300px; }
.profile-right { flex: 2; min-width: 400px; }

.user-profile-layout { display: flex; align-items: center; gap: 20px; }
.large-avatar { background-color: #007bff; font-size: 32px; color: #fff; }
.user-info h3 { margin: 0 0 5px 0; font-size: 24px; color: #343a40; }
.user-role { margin: 0 0 15px 0; color: #6c757d; font-size: 14px; }

.card-header { display: flex; align-items: center; gap: 8px; font-weight: bold; color: #343a40; font-size: 16px; }
.guide-content p { color: #6c757d; line-height: 1.8; font-size: 14px; margin-bottom: 12px; background: #f8f9fa; padding: 10px 15px; border-radius: 8px; }
.guide-content strong { color: #007bff; }
:deep(.el-timeline-item__content) { line-height: 1.6; }
</style>