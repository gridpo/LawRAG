<template>
  <div class="login-container">
    <div class="login-card">
      
      <div class="card-left">
        <div class="brand-info">
          <div class="logo-box" title="LawRAG">
            <span class="logo-icon">⚖️</span>
          </div>
          <h2>LawRAG 法律助手</h2>
          <p>您专业的智能法律援助与对话中心</p>
        </div>
        <div class="decoration-circles"></div>
      </div>

      <div class="card-right">
        <el-tabs v-model="activeTab" class="custom-tabs">
          <el-tab-pane label="登 录" name="login">
            <div class="form-wrapper">
              <h3 class="welcome-text">欢迎回来 👋</h3>
              <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef" size="large">
                
                <el-form-item prop="username">
                  <el-input 
                    v-model="loginForm.username" 
                    placeholder="请输入账号" 
                    :prefix-icon="User" />
                </el-form-item>

                <el-form-item prop="password">
                  <el-input 
                    v-model="loginForm.password" 
                    type="password" 
                    placeholder="请输入密码" 
                    :prefix-icon="Lock"
                    show-password />
                </el-form-item>

                <div class="form-actions">
                  <el-checkbox v-model="rememberMe">记住我</el-checkbox>
                  <el-link type="primary" :underline="false">忘记密码？</el-link>
                </div>

                <el-button type="primary" class="submit-btn" :loading="loading" @click="handleLogin">
                  登 录
                </el-button>
              </el-form>
            </div>
          </el-tab-pane>

          <el-tab-pane label="注 册" name="register">
            <div class="form-wrapper">
              <h3 class="welcome-text">创建新账号 🚀</h3>
              <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" size="large">
                
                <el-form-item prop="username">
                  <el-input 
                    v-model="registerForm.username" 
                    placeholder="设置昵称/账号" 
                    :prefix-icon="User" />
                </el-form-item>

                <el-form-item prop="email">
                  <el-input 
                    v-model="registerForm.email" 
                    placeholder="请输入邮箱" 
                    :prefix-icon="Message" />
                </el-form-item>

                <el-form-item prop="password">
                  <el-input 
                    v-model="registerForm.password" 
                    type="password" 
                    placeholder="设置密码 (至少6位)" 
                    :prefix-icon="Lock"
                    show-password />
                </el-form-item>

                <el-form-item prop="confirmPassword">
                  <el-input 
                    v-model="registerForm.confirmPassword" 
                    type="password" 
                    placeholder="确认密码" 
                    :prefix-icon="Lock"
                    show-password />
                </el-form-item>

                <div class="agreement">
                  <el-checkbox v-model="agreed">我已阅读并同意</el-checkbox>
                  <el-link type="primary" :underline="false">《服务协议》</el-link> 和 
                  <el-link type="primary" :underline="false">《隐私政策》</el-link>
                </div>

                <el-button type="primary" class="submit-btn" :loading="loading" @click="handleRegister">
                  注 册
                </el-button>
              </el-form>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useUserStore } from '../store/user'
import request from '../api/request'

const router = useRouter()
const userStore = useUserStore()

// 状态控制
const activeTab = ref('login')
const loading = ref(false)
const rememberMe = ref(false)
const agreed = ref(false)

// 表单 Ref
const loginFormRef = ref(null)
const registerFormRef = ref(null)

// 登录数据与校验
const loginForm = reactive({ username: '', password: '' })
const loginRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 注册数据与校验
const registerForm = reactive({ username: '', email: '', password: '', confirmPassword: '' })
const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致!'))
  } else {
    callback()
  }
}
const registerRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }, { min: 3, message: '长度至少 3 个字符', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }, { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: validatePass2, trigger: 'blur' }]
}

// 登录逻辑
const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        // FastAPI OAuth2 默认接收 formData 格式
        const formData = new URLSearchParams()
        formData.append('username', loginForm.username)
        formData.append('password', loginForm.password)
        
        const res = await request.post('/auth/login', formData)
        
        // 保存 Token 和用户信息
        userStore.setToken(res.access_token)
        userStore.setUsername(loginForm.username)
        
        ElMessage.success('登录成功！') // 对应设计：淡入淡出 Toast
        router.push('/') // 跳转到聊天主界面
      } catch (error) {
        // 错误已在 request.js 中拦截并提示
      } finally {
        loading.value = false
      }
    }
  })
}

// 注册逻辑
const handleRegister = async () => {
  if (!agreed.value) {
    return ElMessage.warning('请先阅读并同意服务协议与隐私政策')
  }
  if (!registerFormRef.value) return
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await request.post('/auth/register', {
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password
        })
        ElMessage.success('注册成功，请登录！')
        activeTab.value = 'login' // 注册成功后自动切换到登录卡片
        loginForm.username = registerForm.username // 自动填入账号
      } catch (error) {
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
/* 严格按照你的设计规范进行的 CSS 实现 */

/* 1. 全局背景：浅灰色 */
.login-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f8f9fa; 
}

/* 2. 中央卡片：大白容器，20px圆角，悬浮阴影 */
.login-card {
  display: flex;
  width: 900px;
  height: 540px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  overflow: hidden; /* 保证子元素的圆角不溢出 */
}

/* 左侧宣传区 */
.card-left {
  flex: 1;
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); /* 主色调：蓝色 */
  color: white;
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.brand-info {
  position: relative;
  z-index: 2;
}

.logo-box {
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 40px;
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
  cursor: pointer;
}

.logo-icon {
  font-size: 22px;
}

.card-left h2 {
  font-size: 28px;
  margin-bottom: 10px;
  font-weight: 600;
}

.card-left p {
  font-size: 16px;
  opacity: 0.8;
}

/* 简单的左侧装饰背景 */
.decoration-circles {
  position: absolute;
  bottom: -50px;
  right: -50px;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: -50px -50px 0 20px rgba(255, 255, 255, 0.05);
}

/* 右侧功能区 */
.card-right {
  width: 450px;
  padding: 40px 50px;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

.welcome-text {
  color: #343a40; /* 文字色：深灰 */
  margin-bottom: 25px;
  font-size: 22px;
}

/* 覆盖 Element Plus 的默认样式，实现 8px 圆角和颜色规范 */
:deep(.el-input__wrapper) {
  border-radius: 8px; /* 输入框圆角 */
  box-shadow: 0 0 0 1px #e0e0e0 inset; /* 边框：极淡的灰色 */
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #007bff inset; /* 聚焦时边框变为主色调 */
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  margin-top: -10px;
}

.agreement {
  font-size: 13px;
  color: #6c757d; /* 辅助说明：浅灰 */
  margin-bottom: 20px;
  margin-top: -10px;
}

.submit-btn {
  width: 100%;
  border-radius: 8px; /* 按钮圆角 */
  font-size: 16px;
  height: 44px;
  background-color: #007bff; /* 主色调 */
  border: none;
  margin-top: 10px;
}

.submit-btn:hover {
  background-color: #0056b3;
}

/* 标签页切换样式优化 */
:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #e0e0e0;
}
:deep(.el-tabs__item) {
  font-size: 16px;
  color: #6c757d;
}
:deep(.el-tabs__item.is-active) {
  color: #007bff;
  font-weight: 600;
}
:deep(.el-tabs__active-bar) {
  background-color: #007bff;
}
</style>