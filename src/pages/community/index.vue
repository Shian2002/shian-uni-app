<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="page-wrap">
      <!-- 社区头部 -->
      <section class="tool-hero">
        <view class="tool-hero-content">
          <view class="section-tag">交流社区</view>
          <view class="tool-hero-title">民俗文化探讨 · 同好交流</view>
          <view class="tool-hero-desc">分享排盘心得 · 交流应验经验 · 共同学习进步</view>
        </view>
      </section>

      <section class="section">
        <!-- 合规声明 -->
        <view class="compliance-notice">民俗文化探讨，不构成命运预测承诺</view>

        <!-- 搜索 + 发帖 -->
        <view class="search-row">
          <view class="search-box">
            <text class="search-icon">🔍</text>
            <view id="comSearchQuery-wrap" class="dom-input-wrap"></view>
          </view>
          <view class="btn btn-accent" @tap="openPostModal" @click="openPostModal">✎ 发帖</view>
          <view class="header-icons">
            <text class="notif-bell" @tap="toggleNotifPanel" @click="toggleNotifPanel">🔔<text class="notif-badge" v-if="unreadCount > 0">{{ unreadCount }}</text></text>
            <text class="admin-gear" v-if="isAdmin" @tap="showAdminPanel = true" @click="showAdminPanel = true">⚙️</text>
          </view>
        </view>

        <!-- 通知面板 -->
        <view class="notif-panel" v-if="notifPanelOpen">
          <view class="notif-panel-header">
            <text class="notif-panel-title">通知</text>
            <text class="notif-read-all" @tap="markAllNotifRead" @click="markAllNotifRead">全部已读</text>
          </view>
          <view class="notif-list">
            <view class="notif-item" v-for="n in notifications" :key="n.id" :class="{ unread: !n.isRead }" @tap="readNotifAndGo(n)" @click="readNotifAndGo(n)">
              <text class="notif-icon">{{ n.type === 'like' ? '❤️' : n.type === 'comment' ? '💬' : n.type === 'reply' ? '↩️' : '📢' }}</text>
              <view class="notif-body">
                <text class="notif-content">{{ n.content }}</text>
                <text class="notif-time">{{ n.time }}</text>
              </view>
            </view>
            <view class="notif-empty" v-if="!notifications.length">暂无通知</view>
          </view>
        </view>

        <!-- 分类tab -->
        <view class="category-tab">
          <view class="ctab" :class="{ active: activeCategory === cat }" v-for="cat in categories" :key="cat" @tap="switchComCategory(cat, $event)" @click="switchComCategory(cat, $event)">{{ cat }}</view>
        </view>

        <!-- 排序选项 -->
        <view class="sort-tab">
          <view class="stab" :class="{ active: activeSort === s.key }" v-for="s in sortOptions" :key="s.key" @tap="switchSort(s.key)" @click="switchSort(s.key)">{{ s.label }}</view>
        </view>

        <!-- 帖子列表 -->
        <view class="post-list" v-if="!postDetailView && !userProfileView">
          <view class="com-loading" v-if="comLoading && !posts.length">加载中...</view>
          <view class="community-post-card" v-for="post in filteredPosts" :key="post.id" @tap="openPostDetail(post.id)" @click="openPostDetail(post.id)">
            <view class="post-header">
              <view class="post-avatar" @tap.stop="openUserProfile(post.userId)">{{ post.avatar }}</view>
              <view class="post-user-info" @tap.stop="openUserProfile(post.userId)">
                <view class="post-username">{{ post.username }}</view>
                <view class="post-meta">{{ post.time }} · {{ post.category }}</view>
              </view>
              <view class="post-badge" v-if="post.isFeatured">精华</view>
              <view class="post-badge badge-pin" v-if="post.isPinned">置顶</view>
              <view class="post-badge badge-hot" v-else-if="post.hot">热门</view>
            </view>
            <view class="post-title">{{ post.title }}</view>
            <view class="post-content" v-if="post.content">{{ post.content }}</view>
            <view class="post-thumb" v-if="post.imageUrl">
              <image :src="post.imageUrl" mode="widthFix" class="post-thumb-img" />
            </view>
            <view class="post-actions">
              <text @tap.stop="togglePostLike(post.id)">{{ post.isLiked ? '❤️' : '🤍' }} {{ post.likes }}</text>
              <text>💬 {{ post.comments }}</text>
              <text @tap.stop="toggleBookmark(post.id)">{{ bookmarkedIds.has(post.id) ? '⭐' : '☆' }} {{ bookmarkedIds.has(post.id) ? '已收藏' : '收藏' }}</text>
            </view>
          </view>
          <view class="com-loading" v-if="comLoading && posts.length">加载中...</view>
          <view class="com-empty" v-if="!comLoading && !posts.length">暂无帖子，快来发第一篇吧~</view>
          <view class="com-load-more" v-if="comHasMore && !comLoading" @tap="loadMorePosts" @click="loadMorePosts">加载更多</view>
        </view>

        <!-- 用户主页 -->
        <view class="user-profile" v-if="userProfileView">
          <view class="pd-back" @tap="closeUserProfile" @click="closeUserProfile">← 返回列表</view>
          <view class="up-header" v-if="userProfile">
            <view class="up-avatar">👤</view>
            <view class="up-info">
              <view class="up-name">{{ userProfile.username }}</view>
              <view class="up-stats">发布了 {{ userProfile.postCount }} 篇帖子</view>
            </view>
          </view>
          <view class="up-posts">
            <view class="community-post-card" v-for="post in userProfilePosts" :key="post.id" @tap="openPostDetail(post.id)" @click="openPostDetail(post.id)">
              <view class="post-header">
                <view class="post-avatar">👤</view>
                <view class="post-user-info">
                  <view class="post-username">{{ post.username }}</view>
                  <view class="post-meta">{{ post.time }} · {{ post.category }}</view>
                </view>
                <view class="post-badge" v-if="post.isFeatured">精华</view>
              </view>
              <view class="post-title">{{ post.title }}</view>
              <view class="post-content" v-if="post.content">{{ post.content }}</view>
              <view class="post-actions">
                <text>❤️ {{ post.likes }}</text>
                <text>💬 {{ post.comments }}</text>
              </view>
            </view>
            <view class="com-empty" v-if="!comLoading && !userProfilePosts.length">该用户暂无帖子</view>
            <view class="com-load-more" v-if="userProfileHasMore && !comLoading" @tap="loadMoreUserPosts" @click="loadMoreUserPosts">加载更多</view>
          </view>
        </view>

        <!-- 帖子详情 -->
        <view class="post-detail" v-if="postDetailView">
          <view class="pd-back" @tap="closePostDetail" @click="closePostDetail">← 返回列表</view>
          <view class="community-post-card" v-if="currentPost">
            <view class="post-header">
              <view class="post-avatar" @tap="openUserProfile(currentPost.userId)" @click="openUserProfile(currentPost.userId)">{{ currentPost.avatar }}</view>
              <view class="post-user-info" @tap="openUserProfile(currentPost.userId)" @click="openUserProfile(currentPost.userId)">
                <view class="post-username">{{ currentPost.username }}</view>
                <view class="post-meta">{{ currentPost.time }} · {{ currentPost.category }}</view>
              </view>
              <view class="post-badge" v-if="currentPost.isFeatured">精华</view>
            </view>
            <view class="post-title" style="font-size:1.125rem;">{{ currentPost.title }}</view>
            <view class="post-content" style="white-space:pre-wrap;">{{ currentPost.content }}</view>
            <view class="post-thumb" v-if="currentPost.imageUrl" style="margin-top:8px;">
              <image :src="currentPost.imageUrl" mode="widthFix" class="post-thumb-img" />
            </view>
            <view class="pd-actions">
              <view class="pd-like-btn" :class="{ liked: currentPost.isLiked }" @tap="togglePostLike(currentPost.id)" @click="togglePostLike(currentPost.id)">
                {{ currentPost.isLiked ? '❤️' : '🤍' }} {{ currentPost.likes }}
              </view>
              <view class="pd-edit-btn" v-if="isOwnPost(currentPost)" @tap="openEditPost" @click="openEditPost">编辑</view>
              <view class="pd-delete-btn" v-if="isOwnPost(currentPost)" @tap="deletePost(currentPost.id)" @click="deletePost(currentPost.id)">删除</view>
              <view class="pd-share-btn" @tap="sharePost(currentPost.id)" @click="sharePost(currentPost.id)">分享</view>
              <view class="pd-report-btn" @tap="showReportModal('post', currentPost.id)" @click="showReportModal('post', currentPost.id)">举报</view>
              <template v-if="isAdmin && currentPost">
                <view class="pd-admin-btn" @tap="adminPinPost(currentPost.id, !currentPost.isPinned)" @click="adminPinPost(currentPost.id, !currentPost.isPinned)">{{ currentPost.isPinned ? '取消置顶' : '置顶' }}</view>
                <view class="pd-admin-btn" @tap="adminFeaturePost(currentPost.id, !currentPost.isFeatured)" @click="adminFeaturePost(currentPost.id, !currentPost.isFeatured)">{{ currentPost.isFeatured ? '取消加精' : '加精' }}</view>
                <view class="pd-admin-btn" @tap="adminHidePost(currentPost.id, true)" @click="adminHidePost(currentPost.id, true)">隐藏</view>
              </template>
            </view>
          </view>

          <!-- 评论区 -->
          <view class="comment-section" v-if="currentPost">
            <view class="comment-title">评论 ({{ (currentPost.commentList || []).length }})</view>
            <view class="comment-item" v-for="c in (currentPost.commentList || [])" :key="c.id">
              <view class="ci-header">
                <text class="ci-author" @tap="openUserProfile(c.userId)">{{ c.username || '匿名' }}</text>
                <text class="ci-time">{{ c.time }}</text>
                <text class="ci-like-btn" :class="{ liked: c.isLiked }" @tap.stop="toggleCommentLike(c)">👍 {{ c.likes || 0 }}</text>
                <text class="ci-delete" v-if="isOwnComment(c)" @tap="deleteComment(c.id, currentPost.id)">删除</text>
              </view>
              <view class="ci-content">{{ c.content }}</view>
              <view class="ci-replies" v-if="c.replies && c.replies.length">
                <view class="comment-item ci-reply" v-for="r in c.replies" :key="r.id">
                  <view class="ci-header">
                    <text class="ci-author" @tap="openUserProfile(r.userId)">{{ r.username || '匿名' }}</text>
                    <text class="ci-time">{{ r.time }}</text>
                    <text class="ci-like-btn" :class="{ liked: r.isLiked }" @tap.stop="toggleCommentLike(r)">👍 {{ r.likes || 0 }}</text>
                    <text class="ci-delete" v-if="isOwnComment(r)" @tap="deleteComment(r.id, currentPost.id)">删除</text>
                  </view>
                  <view class="ci-content">{{ r.content }}</view>
                </view>
              </view>
            </view>
            <view class="comment-empty" v-if="!(currentPost.commentList || []).length">暂无评论，来说点什么吧~</view>
          </view>

          <!-- 评论输入 -->
          <view class="comment-input-row">
            <view id="comCommentText-wrap" class="dom-input-wrap"></view>
            <view class="comment-send-btn" @tap="submitComment">发送</view>
          </view>
        </view>

        <view class="community-hint" v-if="!postDetailView && !userProfileView && posts.length">共 {{ comTotal }} 篇帖子</view>
      </section>
    </view>



    <!-- 发帖弹窗 -->
    <view class="modal-overlay" id="comPostModal">
      <view class="modal-box" style="max-width:500px;">
        <view class="modal-title">发帖</view>
        <view class="field"><text class="field-label">标题</text><view id="comNewPostTitle-wrap" class="dom-input-wrap"></view></view>
        <view class="field"><text class="field-label">内容</text><textarea v-model="newPostContent" class="field-input" style="min-height:100px;resize:vertical;" placeholder="分享你的见解..." /></view>
        <view class="field">
          <text class="field-label">图片（选填）</text>
          <view class="img-upload-row">
            <view class="img-upload-btn" @tap="choosePostImage" v-if="!newPostImageTemp">📷 选择图片</view>
            <view class="img-preview-wrap" v-if="newPostImageTemp">
              <image :src="newPostImageTemp" mode="aspectFill" class="img-preview-thumb" />
              <view class="img-remove-btn" @tap="removePostImage">✕</view>
            </view>
          </view>
        </view>
        <view class="field" style="display:flex;gap:12px;">
          <view style="flex:1;"><text class="field-label">分类</text>
            <select class="form-select-picker" v-model="newPostCatIdx">
              <option v-for="(cat, idx) in categories.slice(1)" :key="idx" :value="idx">{{ cat }}</option>
            </select>
          </view>
          <view style="flex:1;"><text class="field-label">标签</text><view id="comNewPostTags-wrap" class="dom-input-wrap"></view></view>
        </view>
        <view class="modal-error">{{ newPostError }}</view>
        <view class="modal-btns"><view class="btn btn-outline" @tap="closePostModal">取消</view><view class="btn btn-accent" @tap="submitNewPost">发布</view></view>
      </view>
    </view>

    <!-- 免责声明弹窗 -->
    <view class="modal-overlay" id="comDisclaimerModal">
      <view class="modal-box" style="max-width:420px;">
        <view class="modal-title">⚠️ 免责声明</view>
        <view class="disclaimer-text">本站内容仅为民俗文化与传统命理科普参考，不构成任何决策建议。严禁利用本站内容从事封建迷信及违法违规活动。发布内容需遵守法律法规，不得含有封建迷信、违法违规信息。</view>
        <label class="disclaimer-check" @tap="disclaimerAgreed = !disclaimerAgreed">
          <text>{{ disclaimerAgreed ? '☑' : '☐' }} 我已阅读并同意以上声明</text>
        </label>
        <view class="modal-btns"><view class="btn btn-outline" @tap="closeDisclaimerModal">取消</view><view class="btn btn-accent" :style="{ opacity: disclaimerAgreed ? 1 : 0.5 }" @tap="confirmDisclaimer">确认发布</view></view>
      </view>
    </view>

    <!-- 编辑帖子弹窗 -->
    <view class="modal-overlay" id="comEditModal">
      <view class="modal-box" style="max-width:500px;">
        <view class="modal-title">编辑帖子</view>
        <view class="field"><text class="field-label">标题</text><view id="comEditTitle-wrap" class="dom-input-wrap"></view></view>
        <view class="field"><text class="field-label">内容</text><textarea v-model="editPostContent" class="field-input" style="min-height:100px;resize:vertical;" placeholder="分享你的见解..." /></view>
        <view class="field" style="display:flex;gap:12px;">
          <view style="flex:1;"><text class="field-label">分类</text>
            <select class="form-select-picker" v-model="editCatIdx">
              <option v-for="(cat, idx) in editCategories" :key="idx" :value="idx">{{ cat }}</option>
            </select>
          </view>
          <view style="flex:1;"><text class="field-label">标签</text><view id="comEditTags-wrap" class="dom-input-wrap"></view></view>
        </view>
        <view class="modal-error">{{ editPostError }}</view>
        <view class="modal-btns"><view class="btn btn-outline" @tap="closeEditModal">取消</view><view class="btn btn-accent" @tap="submitEditPost">保存</view></view>
      </view>
    </view>

    <!-- 举报弹窗 -->
    <view class="modal-overlay" id="comReportModal">
      <view class="modal-box" style="max-width:420px;">
        <view class="modal-title">举报内容</view>
        <view class="report-reasons">
          <view class="report-reason" v-for="(label, key) in reportReasons" :key="key" @tap="selectedReportReason = key">
            <text>{{ selectedReportReason === key ? '◉' : '○' }} {{ label }}</text>
          </view>
        </view>
        <view class="modal-error">{{ reportError }}</view>
        <view class="modal-btns"><view class="btn btn-outline" @tap="closeReportModal">取消</view><view class="btn btn-accent" @tap="submitReport">提交举报</view></view>
      </view>
    </view>

    <!-- 管理员面板 -->
    <view class="modal-overlay" id="comAdminModal">
      <view class="modal-box" style="max-width:600px;">
        <view class="modal-title">管理面板 - 举报审核</view>
        <view class="admin-report-list">
          <view class="admin-report-item" v-for="r in adminReports" :key="r.id">
            <view class="ar-header">
              <text class="ar-reporter">{{ r.reporterName }} 举报了 {{ r.targetType }}#{{ r.targetId }}</text>
              <text class="ar-time">{{ r.time }}</text>
            </view>
            <text class="ar-reason">原因: {{ r.reasonLabel }}</text>
            <view class="ar-actions">
              <view class="btn btn-outline" style="font-size:0.7rem;padding:4px 10px;" @tap="resolveReport(r.id, 'resolve')">确认处理</view>
              <view class="btn btn-outline" style="font-size:0.7rem;padding:4px 10px;" @tap="resolveReport(r.id, 'dismiss')">驳回</view>
            </view>
          </view>
          <view class="notif-empty" v-if="!adminReports.length">暂无待处理举报</view>
        </view>
        <view class="modal-btns"><view class="btn btn-outline" @tap="closeAdminPanel">关闭</view></view>
      </view>
    </view>


  </view>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopNav from '@/components/TopNav.vue'

const theme = ref(uni.getStorageSync('xc_theme') || 'dark')
function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  uni.setStorageSync('xc_theme', theme.value)
  try {
    document.documentElement.setAttribute('data-theme', theme.value); document.body.setAttribute('data-theme', theme.value); const root = document.querySelector('.page-root')
    if (root) root.setAttribute('data-theme', theme.value)
    const icon = document.getElementById('themeToggleIcon')
    if (icon) icon.textContent = theme.value === 'dark' ? '🌙' : '☀️'
  } catch(_) {}
}

// ── DOM helper: create native input (Vue 3.4.21 render fix) ──
function createNativeInput(wrapId, type, placeholder) {
  var wrap = document.getElementById(wrapId)
  if (!wrap) return null
  var inp = document.createElement('input')
  inp.type = type
  inp.id = wrapId.replace('-wrap', '')
  if (placeholder) inp.placeholder = placeholder
  inp.style.cssText = 'width:100%;padding:10px 14px;border-radius:10px;background:var(--input-bg);border:1px solid var(--input-border);color:var(--text-1);font-size:0.875rem;outline:none;box-sizing:border-box;transition:border-color 0.2s,box-shadow 0.2s'
  if (wrapId === 'comSearchQuery-wrap') inp.style.paddingLeft = '40px'
  inp.onfocus = function() { this.style.borderColor = 'var(--accent)'; this.style.boxShadow = '0 0 0 2px var(--accent-glow)' }
  inp.onblur = function() { this.style.borderColor = 'var(--input-border)'; this.style.boxShadow = 'none' }
  if (type === 'text') inp.setAttribute('maxlength', '100')
  if (type === 'number') { inp.min = '0'; inp.max = '999' }
  wrap.appendChild(inp)
  return inp
}

function getDomVal(id) { var el = document.getElementById(id); return el ? el.value : '' }
function setDomVal(id, val) { var el = document.getElementById(id); if (el) el.value = val }

// Force computed re-evaluation on DOM input changes
const _searchRefreshKey = ref(0)

const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })
function closePostModal() { showPostModal.value = false; try { document.getElementById('comPostModal')?.classList.remove('open') } catch(_) {} }
function closeDisclaimerModal() { showDisclaimer.value = false; try { document.getElementById('comDisclaimerModal')?.classList.remove('open') } catch(_) {} }

const searchQuery = ref('')
const showPostModal = ref(false)
const showDisclaimer = ref(false)
function openPostModal() { showPostModal.value = true; try { document.getElementById('comPostModal')?.classList.add('open') } catch(_) {} }
function openDisclaimerModal() { showDisclaimer.value = true; try { document.getElementById('comDisclaimerModal')?.classList.add('open') } catch(_) {} }
const disclaimerAgreed = ref(false)
const categories = ['全部', '分享', '讨论', '求助', '心得']
const activeCategory = ref('全部')
const CATEGORY_LABELS = { '分享': '分享', '讨论': '讨论', '求助': '求助', '心得': '心得', 'share': '分享', 'discuss': '讨论', 'ask': '求助', 'experience': '心得' }
const CATEGORY_API = { '分享': 'share', '讨论': 'discuss', '求助': 'ask', '心得': 'experience' }

const sortOptions = [
  { key: 'latest', label: '最新' },
  { key: 'hot', label: '最热' },
  { key: 'featured', label: '精华' }
]
const activeSort = ref('latest')

function switchSort(key) {
  activeSort.value = key
  comPage.value = 1
  loadPosts()
}

function switchComCategory(cat, event) {
  if (event && event._xcHandled) return
  if (event) event._xcHandled = true
  activeCategory.value = cat
  comPage.value = 1
  loadPosts()
}

const newPostTitle = ref(''); const newPostContent = ref(''); const newPostCatIdx = ref(0)
const newPostTags = ref(''); const newPostError = ref('')
const _pendingPostData = ref(null)
const newPostImageUrl = ref('')
const newPostImageTemp = ref('')

const postDetailView = ref(false)
const currentPostId = ref(null)
const currentPost = ref(null)
const commentText = ref('')

const posts = ref([])
const comLoading = ref(false)
const comPage = ref(1)
const comHasMore = ref(false)
const comTotal = ref(0)

const bookmarkedIds = ref(new Set())
const bookmarkMap = ref({})

const userProfileView = ref(false)
const userProfile = ref(null)
const userProfilePosts = ref([])
const userProfilePage = ref(1)
const userProfileHasMore = ref(false)

const editPostContent = ref('')
const editPostError = ref('')
const editCatIdx = ref(0)
const editCategories = ['分享', '讨论', '求助', '心得']
const editPostId = ref(null)

const notifPanelOpen = ref(false)
const notifications = ref([])
const unreadCount = ref(0)
const isAdmin = ref(false)
const selectedReportReason = ref('')
const reportError = ref('')
const reportTarget = ref({ type: '', id: 0 })
const showAdminPanel = ref(false)
const adminReports = ref([])
const reportReasons = { spam: '垃圾广告', abuse: '辱骂/骚扰', misinformation: '虚假信息', illegal: '违法违规', other: '其他' }

function _formatTime(iso) {
  if (!iso) return ''
  var d = new Date(iso), now = new Date(), diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
  return d.toLocaleDateString('zh-CN')
}

async function loadPosts(append) {
  if (comLoading.value) return
  comLoading.value = true
  try {
    var url = '/api/posts?page=' + comPage.value + '&per_page=20&sort=' + activeSort.value
    if (activeCategory.value !== '全部') {
      var catKey = CATEGORY_API[activeCategory.value]
      if (catKey) url += '&category=' + catKey
    }
    var sq = getDomVal('comSearchQuery')
    if (sq) url += '&tag=' + encodeURIComponent(sq.trim())
    var res = await uni.request({ url: url })
    var d = res.data
    if (d && d.posts) {
      var mapped = d.posts.map(function(p) {
        return {
          id: p.id, avatar: '👤', username: p.username || '匿名', userId: p.userId,
          time: _formatTime(p.createdAt), category: CATEGORY_LABELS[p.category] || p.category,
          title: p.title, content: p.contentPreview || '', likes: p.likesCount || 0, comments: p.commentsCount || 0,
          isLiked: false, hot: (p.likesCount || 0) > 20, isFeatured: !!p.isFeatured, imageUrl: p.imageUrl || '',
          isPinned: !!p.isPinned,
          tags: p.tags || []
        }
      })
      if (append) { posts.value = posts.value.concat(mapped) }
      else { posts.value = mapped }
      comHasMore.value = !!d.has_next
      comTotal.value = d.total || 0
    }
  } catch (e) { console.error('loadPosts error', e) }
  finally { comLoading.value = false }
}

function loadMorePosts() {
  if (!comHasMore.value || comLoading.value) return
  comPage.value++
  loadPosts(true)
}

async function loadBookmarks() {
  if (!uni.getStorageSync('xc_token')) return
  try {
    var res = await uni.request({ url: '/api/collections?type=post' })
    var d = res.data
    if (d && d.collections) {
      var ids = new Set()
      var map = {}
      d.collections.forEach(function(c) {
        ids.add(c.targetId)
        map[c.targetId] = c.id
      })
      bookmarkedIds.value = ids
      bookmarkMap.value = map
    }
  } catch (e) { console.error('loadBookmarks error', e) }
}

async function toggleBookmark(id) {
  if (!uni.getStorageSync('xc_token')) { try { _openLoginModal(); var e = document.getElementById('tnLoginError'); if (e) e.textContent = '' } catch(_) {}; return }
  if (bookmarkedIds.value.has(id)) {
    var cid = bookmarkMap.value[id]
    if (cid) {
      try { await uni.request({ url: '/api/collections/' + cid, method: 'DELETE' }) } catch (e) {}
    }
    bookmarkedIds.value.delete(id)
    delete bookmarkMap.value[id]
    uni.showToast({ title: '已取消收藏', icon: 'none' })
  } else {
    try {
      var res = await uni.request({ url: '/api/collections', method: 'POST', data: { targetType: 'post', targetId: id } })
      var d = res.data
      if (d && d.id) { bookmarkMap.value[id] = d.id }
    } catch (e) {}
    bookmarkedIds.value.add(id)
    uni.showToast({ title: '已收藏', icon: 'success' })
  }
}

function showFooterInfo(type) {
  const info = { about: '时安解忧屋 — 看得懂用得上的民俗命理参考平台', contact: '客服邮箱：support@shian.com', privacy: '我们重视您的隐私，所有命盘数据仅存储在您的设备本地，不会上传至服务器。详细隐私政策请访问关于我们页面。' }
  uni.showModal({ title: type === 'about' ? '关于我们' : type === 'contact' ? '联系方式' : '隐私政策', content: info[type] || '', showCancel: false })
}

function goNav(url, type) {
  var TAB_LIST = ['/pages/index/index', '/pages/qimen/index', '/pages/bazi-index/index', '/pages/tarot/index', '/pages/liuyao/index', '/pages/meihua/index', '/pages/ziwei/index', '/pages/zeji/index', '/pages/calendar/index', '/pages/community/index', '/pages/profile/index']
  var pathOnly = url.split('?')[0]
  if (type === 'switchTab' || TAB_LIST.indexOf(pathOnly) > -1) {
    if (url.indexOf('?') > -1) {
      var queryStr = url.substring(url.indexOf('?'))
      try { sessionStorage.setItem('_nav_query', queryStr) } catch(_) {}
    }
    uni.switchTab({
      url: pathOnly,
      success: function() {
        if (url.indexOf('?') > -1) {
          var q = url.substring(url.indexOf('?'))
          setTimeout(function() { try { uni.$emit('nav-query', q) } catch(_) {} }, 200)
        }
      }
    })
  } else {
    uni.navigateTo({ url })
  }
}

const filteredPosts = computed(() => {
  var list = posts.value
  _searchRefreshKey.value
  return list
})

function isOwnPost(post) { var u = uni.getStorageSync('xc_user_id'); return String(post.userId) === String(u) }
function isOwnComment(c) { var u = uni.getStorageSync('xc_user_id'); return String(c.userId) === String(u) }

async function openPostDetail(id) {
  currentPostId.value = id
  postDetailView.value = true
  setTimeout(function() {
    if (!document.getElementById('comCommentText')) {
      createNativeInput('comCommentText-wrap', 'text', '发表评论...')
      var ci = document.getElementById('comCommentText')
      if (ci) ci.addEventListener('keydown', function(e) { if (e.key === 'Enter') { e.preventDefault(); submitComment() } })
    }
  }, 50)
  try {
    var res = await uni.request({ url: '/api/posts/' + id })
    var d = res.data
    if (d && !d.error) {
      currentPost.value = {
        id: d.id, avatar: '👤', username: d.username || '匿名', userId: d.userId,
        time: _formatTime(d.createdAt),
        category: CATEGORY_LABELS[d.category] || d.category,
        title: d.title, content: d.content, likes: d.likesCount || 0,
        comments: (d.comments || []).length, isLiked: !!d.liked,
        isFeatured: !!d.isFeatured, imageUrl: d.imageUrl || '',
        isPinned: !!d.isPinned, isHidden: !!d.isHidden,
        tags: d.tags || [],
        commentList: (d.comments || []).map(function(c) {
          return {
            id: c.id, username: c.username || '匿名', userId: c.userId,
            content: c.content, time: _formatTime(c.createdAt),
            likes: c.likesCount || 0, isLiked: !!c.liked,
            replies: (c.replies || []).map(function(r) {
              return { id: r.id, username: r.username || '匿名', userId: r.userId, content: r.content, time: _formatTime(r.createdAt), likes: r.likesCount || 0, isLiked: !!r.liked }
            })
          }
        })
      }
    }
  } catch (e) { console.error('openPostDetail error', e) }
}

function closePostDetail() {
  postDetailView.value = false; currentPost.value = null; currentPostId.value = null; setDomVal('comCommentText', '')
}

async function togglePostLike(id) {
  if (!uni.getStorageSync('xc_token')) { try { _openLoginModal(); var e = document.getElementById('tnLoginError'); if (e) e.textContent = '' } catch(_) {}; return }
  try {
    var res = await uni.request({ url: '/api/posts/' + id + '/like', method: 'POST' })
    var d = res.data
    if (d.liked !== undefined && currentPost.value) {
      currentPost.value.isLiked = d.liked
      currentPost.value.likes = d.likesCount || currentPost.value.likes
      var btn = document.querySelector('.pd-like-btn')
      if (btn) { if (d.liked) btn.classList.add('liked'); else btn.classList.remove('liked') }
    }
    var p = posts.value.find(function(p) { return p.id === id })
    if (p) { p.isLiked = d.liked; p.likes = d.likesCount || p.likes }
  } catch (e) { console.error('like error', e) }
}

async function submitComment() {
  var ct = getDomVal('comCommentText')
  if (!ct.trim()) return
  if (!uni.getStorageSync('xc_token')) { try { _openLoginModal(); var e = document.getElementById('tnLoginError'); if (e) e.textContent = '' } catch(_) {}; return }
  const postId = currentPostId.value
  try {
    const res = await uni.request({ url: `/api/posts/${postId}/comments`, method: 'POST', data: { content: ct.trim() } })
    const d = res.data
    if (d.error) { uni.showToast({ title: d.error, icon: 'none' }); return }
    setDomVal('comCommentText', '')
    openPostDetail(postId) // 刷新
  } catch (e) { uni.showToast({ title: '评论失败', icon: 'none' }) }
}

async function deletePost(id) {
  const [err] = await uni.showModal({ title: '确认', content: '确定删除该帖子？' })
  if (err || !err.confirm) return
  try {
    await uni.request({ url: '/api/posts/' + id, method: 'DELETE' })
    var idx = posts.value.findIndex(function(p) { return p.id === id })
    if (idx >= 0) posts.value.splice(idx, 1)
    closePostDetail()
    uni.showToast({ title: '已删除', icon: 'success' })
  } catch (e) { uni.showToast({ title: '删除失败', icon: 'none' }) }
}

async function deleteComment(commentId, postId) {
  const [err] = await uni.showModal({ title: '确认', content: '确定删除该评论？' })
  if (err || !err.confirm) return
  try {
    await uni.request({ url: `/api/comments/${commentId}`, method: 'DELETE' })
    openPostDetail(postId) // 刷新
  } catch (e) { uni.showToast({ title: '删除失败', icon: 'none' }) }
}

async function openUserProfile(uid) {
  if (!uid) return
  userProfileView.value = true
  userProfilePosts.value = []
  userProfilePage.value = 1
  userProfileHasMore.value = false
  comLoading.value = true
  try {
    var res = await uni.request({ url: '/api/users/' + uid + '/posts?page=1&per_page=20' })
    var d = res.data
    if (d && d.user) {
      userProfile.value = { username: d.user.username, postCount: d.total || 0 }
      userProfilePosts.value = (d.posts || []).map(function(p) {
        return {
          id: p.id, username: d.user.username, userId: p.userId,
          time: _formatTime(p.createdAt), category: CATEGORY_LABELS[p.category] || p.category,
          title: p.title, content: p.contentPreview || '', likes: p.likesCount || 0,
          comments: p.commentsCount || 0, isFeatured: !!p.isFeatured, imageUrl: p.imageUrl || ''
        }
      })
      userProfileHasMore.value = !!d.has_next
    }
  } catch (e) { console.error('openUserProfile error', e) }
  finally { comLoading.value = false }
}

function closeUserProfile() {
  userProfileView.value = false
  userProfile.value = null
  userProfilePosts.value = []
}

async function loadMoreUserPosts() {
  if (!userProfile.value || comLoading.value) return
  userProfilePage.value++
  comLoading.value = true
  try {
    var uid = userProfilePosts.value[0] ? userProfilePosts.value[0].userId : null
    if (!uid) return
    var res = await uni.request({ url: '/api/users/' + uid + '/posts?page=' + userProfilePage.value + '&per_page=20' })
    var d = res.data
    if (d && d.posts) {
      var mapped = (d.posts || []).map(function(p) {
        return {
          id: p.id, username: d.user.username, userId: p.userId,
          time: _formatTime(p.createdAt), category: CATEGORY_LABELS[p.category] || p.category,
          title: p.title, content: p.contentPreview || '', likes: p.likesCount || 0,
          comments: p.commentsCount || 0, isFeatured: !!p.isFeatured, imageUrl: p.imageUrl || ''
        }
      })
      userProfilePosts.value = userProfilePosts.value.concat(mapped)
      userProfileHasMore.value = !!d.has_next
    }
  } catch (e) { console.error('loadMoreUserPosts error', e) }
  finally { comLoading.value = false }
}

function openEditPost() {
  if (!currentPost.value) return
  editPostId.value = currentPost.value.id
  editPostContent.value = currentPost.value.content
  editPostError.value = ''
  var catLabel = currentPost.value.category
  editCatIdx.value = editCategories.indexOf(catLabel)
  if (editCatIdx.value < 0) editCatIdx.value = 0
  try { document.getElementById('comEditModal')?.classList.add('open') } catch(_) {}
  setTimeout(function() {
    setDomVal('comEditTitle', currentPost.value.title)
    var tags = (currentPost.value.tags || []).join(',')
    setDomVal('comEditTags', tags)
  }, 50)
}

function closeEditModal() {
  try { document.getElementById('comEditModal')?.classList.remove('open') } catch(_) {}
  editPostError.value = ''
}

async function submitEditPost() {
  var title = getDomVal('comEditTitle')
  var content = editPostContent.value.trim()
  if (!title.trim() || !content) { editPostError.value = '标题和内容不能为空'; return }
  var catKey = CATEGORY_API[editCategories[editCatIdx.value]] || 'share'
  var tagsStr = getDomVal('comEditTags')
  var tags = tagsStr ? tagsStr.split(/[,，]/).map(function(t) { return t.trim() }).filter(Boolean) : []
  try {
    var res = await uni.request({
      url: '/api/posts/' + editPostId.value, method: 'PUT',
      data: { title: title.trim(), content: content, category: catKey, tags: tags }
    })
    var d = res.data
    if (d.error) { editPostError.value = d.error; return }
    closeEditModal()
    uni.showToast({ title: '编辑成功', icon: 'success' })
    openPostDetail(editPostId.value)
    comPage.value = 1
    loadPosts()
  } catch (e) { editPostError.value = '编辑失败，请重试' }
}

async function toggleCommentLike(c) {
  if (!uni.getStorageSync('xc_token')) { try { _openLoginModal() } catch(_) {}; return }
  try {
    var res = await uni.request({ url: '/api/comments/' + c.id + '/like', method: 'POST' })
    var d = res.data
    if (d.liked !== undefined) {
      c.isLiked = d.liked
      c.likes = d.likesCount || 0
    }
  } catch (e) { console.error('comment like error', e) }
}

function toggleNotifPanel() {
  notifPanelOpen.value = !notifPanelOpen.value
  if (notifPanelOpen.value) loadNotifications()
}

async function loadNotifications() {
  if (!uni.getStorageSync('xc_token')) return
  try {
    var res = await uni.request({ url: '/api/notifications' })
    var d = res.data
    if (d.notifications) {
      notifications.value = d.notifications.map(function(n) {
        return { id: n.id, type: n.type, content: n.content || '新通知', isRead: n.isRead, postId: n.postId, time: _formatTime(n.createdAt) }
      })
      unreadCount.value = d.unreadCount || 0
    }
  } catch (e) { console.error('loadNotifications error', e) }
}

async function markAllNotifRead() {
  try {
    await uni.request({ url: '/api/notifications/read', method: 'POST' })
    loadNotifications()
  } catch (e) { console.error('markAllNotifRead error', e) }
}

async function readNotifAndGo(n) {
  if (!n.isRead) {
    try { await uni.request({ url: '/api/notifications/' + n.id + '/read', method: 'POST' }) } catch (_) {}
  }
  notifPanelOpen.value = false
  if (n.postId) openPostDetail(n.postId)
}

function startNotifPolling() {
  loadNotifications()
  setInterval(function() { loadNotifications() }, 30000)
}

function showReportModal(type, id) {
  reportTarget.value = { type: type, id: id }
  selectedReportReason.value = ''
  reportError.value = ''
  try { document.getElementById('comReportModal')?.classList.add('open') } catch(_) {}
}

function closeReportModal() {
  try { document.getElementById('comReportModal')?.classList.remove('open') } catch(_) {}
  reportError.value = ''
}

async function submitReport() {
  if (!selectedReportReason.value) { reportError.value = '请选择举报原因'; return }
  try {
    var res = await uni.request({
      url: '/api/reports', method: 'POST',
      data: { targetType: reportTarget.value.type, targetId: reportTarget.value.id, reason: selectedReportReason.value }
    })
    var d = res.data
    if (d.error) { reportError.value = d.error; return }
    closeReportModal()
    uni.showToast({ title: '举报已提交', icon: 'success' })
  } catch (e) { reportError.value = '提交失败，请重试' }
}

async function loadAdminReports() {
  try {
    var res = await uni.request({ url: '/api/admin/reports?status=pending' })
    var d = res.data
    if (d.reports) {
      adminReports.value = d.reports.map(function(r) {
        return { id: r.id, reporterName: r.reporterName, targetType: r.targetType, targetId: r.targetId, reason: r.reason, reasonLabel: reportReasons[r.reason] || r.reason, status: r.status, time: _formatTime(r.createdAt) }
      })
    }
  } catch (e) { console.error('loadAdminReports error', e) }
}

async function resolveReport(rid, action) {
  try {
    var res = await uni.request({
      url: '/api/admin/reports/' + rid + '/resolve', method: 'POST',
      data: { action: action }
    })
    if (res.data.ok) loadAdminReports()
    else uni.showToast({ title: res.data.error || '操作失败', icon: 'none' })
  } catch (e) { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

function closeAdminPanel() {
  showAdminPanel.value = false
  try { document.getElementById('comAdminModal')?.classList.remove('open') } catch(_) {}
}

async function sharePost(pid) {
  try {
    var res = await uni.request({ url: '/api/posts/' + pid + '/share', method: 'POST' })
    var d = res.data
    if (d.shareUrl) {
      uni.setClipboardData({ data: d.shareUrl })
      uni.showToast({ title: '链接已复制', icon: 'success' })
    }
  } catch (e) { uni.showToast({ title: '分享失败', icon: 'none' }) }
}

async function adminPinPost(pid, pinned) {
  try {
    var res = await uni.request({ url: '/api/admin/posts/' + pid + '/pin', method: 'POST', data: { pinned: pinned } })
    if (res.data.ok) { comPage.value = 1; loadPosts(); uni.showToast({ title: pinned ? '已置顶' : '已取消置顶', icon: 'success' }) }
  } catch (e) { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

async function adminFeaturePost(pid, featured) {
  try {
    var res = await uni.request({ url: '/api/admin/posts/' + pid + '/feature', method: 'POST', data: { featured: featured } })
    if (res.data.ok) { comPage.value = 1; loadPosts(); uni.showToast({ title: featured ? '已加精' : '已取消加精', icon: 'success' }) }
  } catch (e) { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

async function adminHidePost(pid, hidden) {
  try {
    var res = await uni.request({ url: '/api/admin/posts/' + pid + '/hide', method: 'POST', data: { hidden: hidden } })
    if (res.data.ok) { comPage.value = 1; loadPosts(); uni.showToast({ title: '已隐藏', icon: 'success' }) }
  } catch (e) { uni.showToast({ title: '操作失败', icon: 'none' }) }
}

function choosePostImage() {
  uni.chooseImage({
    count: 1, sizeType: ['compressed'], sourceType: ['album', 'camera'],
    success: function(res) {
      var tempPath = res.tempFilePaths[0]
      newPostImageTemp.value = tempPath
    }
  })
}

function removePostImage() {
  newPostImageTemp.value = ''
  newPostImageUrl.value = ''
}

function submitNewPost() {
  var title = getDomVal('comNewPostTitle'), content = newPostContent.value.trim()
  if (!title.trim() || !content) { newPostError.value = '标题和内容不能为空'; return }
  if (!uni.getStorageSync('xc_token')) { try { _openLoginModal(); var e = document.getElementById('tnLoginError'); if (e) e.textContent = '' } catch(_) {}; return }
  _pendingPostData.value = {
    title: title.trim(),
    content: content,
    category: categories[newPostCatIdx.value + 1],
    tags: getDomVal('comNewPostTags') ? getDomVal('comNewPostTags').split(/[,，]/).map(t => t.trim()).filter(Boolean) : [],
    imageTemp: newPostImageTemp.value
  }
  openDisclaimerModal()
}

async function confirmDisclaimer() {
  if (!disclaimerAgreed.value) return
  showDisclaimer.value = false; disclaimerAgreed.value = false
  try { document.getElementById('comDisclaimerModal')?.classList.remove('open') } catch(_) {}
  if (!_pendingPostData.value) return
  var data = _pendingPostData.value; _pendingPostData.value = null
  var catKey = CATEGORY_API[data.category] || 'share'
  try {
    var imageUrl = ''
    if (data.imageTemp) {
      try {
        var upRes = await new Promise(function(resolve, reject) {
          uni.uploadFile({
            url: '/api/upload',
            filePath: data.imageTemp,
            name: 'file',
            success: resolve,
            fail: reject
          })
        })
        var upData = typeof upRes.data === 'string' ? JSON.parse(upRes.data) : upRes.data
        if (upData.url) imageUrl = upData.url
      } catch (e) { console.error('upload error', e) }
    }
    var postData = { title: data.title, content: data.content, category: catKey, tags: data.tags }
    if (imageUrl) postData.imageUrl = imageUrl
    var res = await uni.request({ url: '/api/posts', method: 'POST', data: postData })
    var d = res.data
    if (d.error) { newPostError.value = d.error; return }
    showPostModal.value = false
    try { document.getElementById('comPostModal')?.classList.remove('open') } catch(_) {}
    setDomVal('comNewPostTitle', ''); newPostContent.value = ''; setDomVal('comNewPostTags', ''); newPostError.value = ''
    newPostImageTemp.value = ''; newPostImageUrl.value = ''
    uni.showToast({ title: '发布成功', icon: 'success' })
    comPage.value = 1
    loadPosts()
  } catch (e) { newPostError.value = '发布失败，请重试' }
}

onMounted(async function() {
  // 阻止触屏设备上 @tap + @click 双重触发
  window.__xc_lastTap = 0
  document.addEventListener('touchstart', function() { window.__xc_lastTap = Date.now() }, {passive: true})
  document.addEventListener('click', function(e) {
    if (window.__xc_lastTap && Date.now() - window.__xc_lastTap < 600) {
      e._xcHandled = true
    }
  }, true)

  createNativeInput('comSearchQuery-wrap', 'text', '搜索帖子...')
  createNativeInput('comCommentText-wrap', 'text', '发表评论...')
  createNativeInput('comNewPostTitle-wrap', 'text', '帖子标题')
  createNativeInput('comNewPostTags-wrap', 'text', '逗号分隔')
  createNativeInput('comEditTitle-wrap', 'text', '帖子标题')
  createNativeInput('comEditTags-wrap', 'text', '逗号分隔')

  var ci = document.getElementById('comCommentText')
  if (ci) ci.addEventListener('keydown', function(e) { if (e.key === 'Enter') { e.preventDefault(); submitComment() } })

  var si = document.getElementById('comSearchQuery')
  if (si) {
    var _searchTimer = null
    si.addEventListener('input', function() {
      _searchRefreshKey.value++
      clearTimeout(_searchTimer)
      _searchTimer = setTimeout(function() { comPage.value = 1; loadPosts() }, 500)
    })
    si.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') { clearTimeout(_searchTimer); comPage.value = 1; loadPosts() }
    })
  }

  loadPosts()
  loadBookmarks()

  var token = uni.getStorageSync('xc_token')
  if (token) {
    startNotifPolling()
    try {
      var profileRes = await uni.request({ url: '/api/me' })
      if (profileRes.data && profileRes.data.is_admin) isAdmin.value = true
    } catch(_) {}
  }
  if (showAdminPanel.value) loadAdminReports()

  // Safari 桌面兼容 — 原生 click 兜底（uni-app @tap 在无触屏设备的 Safari 上不触发）
  setTimeout(function() {
    document.querySelectorAll('.ctab').forEach(function(_el) {
      _el.addEventListener('click', function(e) {
        if (e._xcHandled) return; e._xcHandled = true
        switchComCategory(_el.textContent.trim(), e)
        document.querySelectorAll('.ctab').forEach(function(o) { o.classList.remove('active') })
        _el.classList.add('active')
      })
    })
    var _sortKeys = { '最新': 'latest', '最热': 'hot', '精华': 'featured' }
    document.querySelectorAll('.stab').forEach(function(_el) {
      _el.addEventListener('click', function(e) {
        var _key = _sortKeys[_el.textContent.trim()]
        if (_key) switchSort(_key)
        document.querySelectorAll('.stab').forEach(function(o) { o.classList.remove('active') })
        _el.classList.add('active')
      })
    })
    // 通用兜底 — 关键交互元素
    var _bell = document.querySelector('.notif-bell')
    if (_bell) _bell.addEventListener('click', function(e) { if (e._xcHandled) return; e._xcHandled = true; toggleNotifPanel() })
  }, 0)

  // 测试桥接 — 允许 E2E 测试直接调用内部函数
  window.__xc = window.__xc || {}
  window.__xc.switchCategory = function(cat) { switchComCategory(cat, null) }
  window.__xc.switchSort = function(key) { switchSort(key) }
})

watch(showAdminPanel, function(v) {
  if (v) {
    loadAdminReports()
    try { document.getElementById('comAdminModal')?.classList.add('open') } catch(_) {}
  } else {
    try { document.getElementById('comAdminModal')?.classList.remove('open') } catch(_) {}
  }
})

onShow(function() {
  if (uni.getStorageSync('xc_token')) {
    loadPosts()
  }
})
</script>

<style scoped>
:root { --ease: cubic-bezier(0.4, 0, 0.2, 1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif; --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; --max-w: 1280px; }
[data-theme="dark"] { --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824; --accent: hsl(38, 60%, 60%); --accent-glow: hsla(38, 60%, 60%, 0.10); --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12); --card-border-hover: rgba(255,255,255,0.18); --card-shadow: 0 16px 48px rgba(0,0,0,0.35); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88); --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0; --accent: hsl(38, 72%, 30%); --accent-glow: hsla(38, 72%, 30%, 0.065); --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045); --card-border-hover: rgba(0,0,0,0.08); --card-shadow: 0 8px 28px rgba(60,40,15,0.055); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88); --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45); }

.page-root { min-height: 100vh; }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%), radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%), linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3)); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%), radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%), linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3)); }
.page-wrap { position: relative; z-index: 1; }

/* 社区页面 */
.section { max-width: var(--max-w); margin: 0 auto; padding: 80px 32px; }
.section-tag { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.6875rem; letter-spacing: 2px; color: var(--accent); background: var(--accent-glow); margin-bottom: 12px; }
.tool-hero { padding: 60px 32px 32px; text-align: center; position: relative; overflow: hidden; }
.tool-hero::before { content: ''; position: absolute; top: -50%; left: -20%; width: 140%; height: 200%; background: radial-gradient(ellipse at center, var(--accent-glow) 0%, transparent 70%); opacity: 0.5; pointer-events: none; }
.tool-hero-content { position: relative; z-index: 1; max-width: var(--max-w); margin: 0 auto; }
.tool-hero-title { font-family: var(--font-serif); font-size: 2rem; font-weight: 400; letter-spacing: 4px; color: var(--text-1); margin-bottom: 12px; }
.tool-hero-desc { font-size: 0.9375rem; color: var(--text-3); letter-spacing: 2px; }

.compliance-notice { background: var(--accent-glow); border: 1px solid var(--card-border); border-radius: var(--radius-md); padding: 12px 18px; margin-bottom: 24px; font-size: 0.8125rem; color: var(--text-2); text-align: center; letter-spacing: 1px; }
.search-row { display: flex; gap: 10px; margin-bottom: 20px; align-items: center; }
.search-box { flex: 1; padding: 0; display: flex; align-items: center; position: relative; min-width: 0; }
.search-icon { position: absolute; left: 14px; z-index: 2; font-size: 0.875rem; line-height: 1; pointer-events: none; }
.search-box .dom-input-wrap { width: 100%; min-width: 0; }
.search-box .dom-input-wrap input { padding-left: 40px !important; }
.form-input { width: 100%; padding: 9px 14px 9px 32px; border-radius: 8px; background: var(--card-bg); border: 1.5px solid var(--card-border); color: var(--text-1); font-size: 0.85rem; outline: none; box-sizing: border-box; }
.category-tab { display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; }
.ctab { padding: 6px 16px; border-radius: 20px; font-size: 0.8125rem; cursor: pointer; background: transparent; color: var(--text-3); border: 1px solid var(--card-border); }
.ctab.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }

.sort-tab { display: flex; gap: 6px; margin-bottom: 20px; flex-wrap: wrap; }
.stab { padding: 4px 12px; border-radius: 16px; font-size: 0.75rem; cursor: pointer; background: transparent; color: var(--text-3); border: 1px solid var(--card-border); }
.stab.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }

.badge-hot { background: rgba(215,125,110,0.12); color: var(--danger); border-color: var(--danger); }

.up-header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; padding: 24px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); }
.up-avatar { width: 56px; height: 56px; border-radius: 50%; background: var(--accent-glow); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
.up-name { font-size: 1.125rem; font-weight: 600; color: var(--text-1); }
.up-stats { font-size: 0.8125rem; color: var(--text-3); margin-top: 4px; }

.pd-edit-btn { padding: 6px 14px; border-radius: 8px; font-size: 0.75rem; color: var(--accent); cursor: pointer; background: var(--accent-glow); border: 1px solid var(--accent); }

.ci-like-btn { font-size: 0.6875rem; color: var(--text-3); cursor: pointer; margin-left: auto; padding: 2px 6px; border-radius: 4px; }
.ci-like-btn.liked { color: var(--accent); background: var(--accent-glow); }
.post-list { display: grid; gap: 16px; }

.community-post-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); padding: 24px; backdrop-filter: blur(16px); transition: all 0.25s var(--ease); }
.community-post-card:hover { border-color: var(--card-border-hover); transform: translateY(-2px); box-shadow: var(--card-shadow); }
.post-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.post-avatar { width: 40px; height: 40px; border-radius: 50%; background: var(--accent-glow); display: flex; align-items: center; justify-content: center; font-size: 1rem; }
.post-user-info { flex: 1; }
.post-username { font-size: 0.875rem; font-weight: 500; color: var(--text-1); }
.post-meta { font-size: 0.6875rem; color: var(--text-3); }
.post-badge { margin-left: auto; padding: 3px 10px; border-radius: 12px; font-size: 0.625rem; background: var(--accent-glow); color: var(--accent); border: 1px solid var(--accent); }
.post-title { font-size: 1rem; margin-bottom: 8px; color: var(--text-1); font-weight: 500; }
.post-content { font-size: 0.8125rem; color: var(--text-3); line-height: 1.6; margin-bottom: 12px; }
.post-actions { display: flex; gap: 16px; font-size: 0.75rem; color: var(--text-3); }
.community-hint { text-align: center; margin-top: 32px; font-size: 0.8125rem; color: var(--text-3); }
.com-loading { text-align: center; padding: 32px; font-size: 0.8125rem; color: var(--text-3); }
.com-empty { text-align: center; padding: 48px 24px; font-size: 0.875rem; color: var(--text-3); }
.com-load-more { text-align: center; padding: 16px; font-size: 0.8125rem; color: var(--accent); cursor: pointer; }

.post-thumb { border-radius: 10px; overflow: hidden; margin-bottom: 12px; }
.post-thumb-img { width: 100%; border-radius: 10px; }

.ci-replies { margin-left: 20px; margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--card-border); }
.ci-reply { border-bottom: none; padding: 8px 0; }

.img-upload-row { margin-top: 6px; }
.img-upload-btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 10px; background: var(--accent-glow); color: var(--accent); font-size: 0.8125rem; border: 1px dashed var(--accent); cursor: pointer; }
.img-preview-wrap { position: relative; display: inline-block; }
.img-preview-thumb { width: 80px; height: 80px; border-radius: 10px; object-fit: cover; }
.img-remove-btn { position: absolute; top: -6px; right: -6px; width: 20px; height: 20px; border-radius: 50%; background: var(--danger); color: #fff; font-size: 0.625rem; display: flex; align-items: center; justify-content: center; cursor: pointer; }

/* 帖子详情 */
.post-detail { max-width: 720px; }
.pd-back { display: inline-block; padding: 8px 16px; margin-bottom: 16px; font-size: 0.875rem; color: var(--accent); cursor: pointer; border-radius: 8px; background: var(--accent-glow); }
.pd-actions { display: flex; gap: 16px; align-items: center; margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--card-border); }
.pd-like-btn { padding: 6px 14px; border-radius: 8px; font-size: 0.875rem; cursor: pointer; background: var(--accent-glow); color: var(--text-2); border: 1px solid var(--card-border); }
.pd-like-btn.liked { background: rgba(215,125,110,0.12); color: var(--danger); border-color: var(--danger); }
.pd-delete-btn { padding: 6px 14px; border-radius: 8px; font-size: 0.75rem; color: var(--danger); cursor: pointer; background: none; border: none; }

/* 评论区 */
.comment-section { margin-top: 24px; }
.comment-title { font-size: 0.9375rem; font-weight: 600; color: var(--text-1); margin-bottom: 12px; }
.comment-item { padding: 12px 0; border-bottom: 1px solid var(--card-border); }
.ci-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.ci-author { font-size: 0.8125rem; font-weight: 500; color: var(--text-1); }
.ci-time { font-size: 0.6875rem; color: var(--text-3); }
.ci-delete { font-size: 0.6875rem; color: var(--danger); margin-left: auto; cursor: pointer; }
.ci-content { font-size: 0.8125rem; color: var(--text-2); line-height: 1.6; }
.comment-empty { text-align: center; padding: 24px; font-size: 0.8125rem; color: var(--text-3); }
.comment-input-row { display: flex; gap: 8px; margin-top: 20px; }
.comment-input { flex: 1; padding: 10px 14px; border: 1.5px solid var(--card-border); border-radius: 10px; font-size: 0.85rem; background: var(--input-bg); color: var(--text-1); outline: none; box-sizing: border-box; }
.comment-send-btn { padding: 10px 18px; border-radius: 10px; font-size: 0.85rem; background: var(--accent); color: #fff; border: none; white-space: nowrap; }

/* 免责声明 */
.disclaimer-text { font-size: 0.8125rem; color: var(--text-2); line-height: 1.8; margin-bottom: 16px; padding: 12px; background: var(--input-bg); border-radius: 10px; }
.disclaimer-check { display: block; text-align: center; font-size: 0.875rem; color: var(--text-2); margin-bottom: 12px; padding: 8px; cursor: pointer; }
.form-select-picker { padding: 9px 12px; border: 1.5px solid var(--card-border); border-radius: 10px; font-size: 0.85rem; background: var(--card-bg); color: var(--text-1); text-align: center; width: 100%; box-sizing: border-box; outline: none; appearance: auto; }

/* 弹窗 */
.modal-overlay { display: none; position: fixed; inset: 0; z-index: 300; background: rgba(0,0,0,0.55); backdrop-filter: blur(8px); align-items: center; justify-content: center; }
.modal-overlay.open { display: flex; }
.modal-box { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; width: 360px; backdrop-filter: blur(40px); box-shadow: var(--card-shadow); }
.modal-title { font-family: var(--font-serif); font-size: 1.1rem; letter-spacing: 2px; text-align: center; margin-bottom: 24px; color: var(--text-1); }
.field { margin-bottom: 14px; }
.field-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; }
.field-input { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error { color: var(--danger); font-size: 0.75rem; text-align: center; margin-top: 10px; min-height: 18px; }

@media (max-width: 768px) {
  .section { padding: 48px 16px; }
  .search-row { flex-direction: column; }

}

.header-icons { display: flex; align-items: center; gap: 12px; margin-left: auto; }
.notif-bell { position: relative; font-size: 1.25rem; cursor: pointer; }
.notif-badge { position: absolute; top: -4px; right: -6px; background: var(--danger); color: #fff; font-size: 0.5625rem; min-width: 16px; height: 16px; border-radius: 8px; text-align: center; line-height: 16px; }
.admin-gear { font-size: 1rem; cursor: pointer; }
.notif-panel { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); padding: 16px; margin-bottom: 16px; backdrop-filter: blur(16px); }
.notif-panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.notif-panel-title { font-weight: 600; color: var(--text-1); }
.notif-read-all { font-size: 0.75rem; color: var(--accent); cursor: pointer; }
.notif-item { display: flex; align-items: center; gap: 8px; padding: 10px; border-radius: 8px; margin-bottom: 4px; cursor: pointer; border: 1px solid var(--card-border); }
.notif-item.unread { background: var(--accent-glow); }
.notif-icon { font-size: 1rem; }
.notif-body { flex: 1; }
.notif-content { font-size: 0.8125rem; color: var(--text-1); display: block; }
.notif-time { font-size: 0.6875rem; color: var(--text-3); }
.notif-empty { text-align: center; color: var(--text-3); font-size: 0.8125rem; padding: 20px; }
.report-reasons { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.report-reason { padding: 8px 12px; border: 1px solid var(--card-border); border-radius: 8px; cursor: pointer; font-size: 0.875rem; color: var(--text-1); }
.badge-pin { background: rgba(115,192,115,0.12); color: #73c073; border-color: #73c073; }
.pd-share-btn { padding: 6px 14px; border-radius: 8px; font-size: 0.75rem; color: var(--accent); cursor: pointer; background: var(--accent-glow); border: 1px solid var(--accent); }
.pd-report-btn { padding: 6px 14px; border-radius: 8px; font-size: 0.75rem; color: var(--text-3); cursor: pointer; background: var(--card-bg); border: 1px solid var(--card-border); }
.pd-admin-btn { padding: 6px 14px; border-radius: 8px; font-size: 0.75rem; color: var(--text-3); cursor: pointer; background: var(--card-bg); border: 1px solid var(--card-border); }
.admin-report-item { padding: 12px; border: 1px solid var(--card-border); border-radius: 8px; margin-bottom: 8px; }
.ar-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.ar-reporter { font-size: 0.8125rem; color: var(--text-1); }
.ar-time { font-size: 0.6875rem; color: var(--text-3); }
.ar-reason { font-size: 0.75rem; color: var(--text-3); display: block; margin-bottom: 8px; }
.ar-actions { display: flex; gap: 8px; }
</style>
