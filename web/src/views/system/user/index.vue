<script setup lang="ts">
import { ref, onMounted, reactive, createVNode } from 'vue'
import {
  pageUsers,
  createUser,
  updateUser,
  deleteUser,
  type UserInfo,
} from '@/api/system-service'
import { message, Modal } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons-vue'
import type { FormInstance } from 'ant-design-vue'

const loading = ref(false)
const dataSource = ref<UserInfo[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  pageSize: 10,
  keyword: '',
})

const columns = [
  { title: '用户账号', dataIndex: 'userCode', key: 'userCode' },
  { title: '用户名称', dataIndex: 'userName', key: 'userName' },
  { title: '手机号', dataIndex: 'mobilePhone', key: 'mobilePhone' },
  { title: '邮箱', dataIndex: 'email', key: 'email' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime' },
  { title: '操作', key: 'action', fixed: 'right', width: 150 },
]

// Modal State
const modalVisible = ref(false)
const modalTitle = ref('新增用户')
const confirmLoading = ref(false)
const formRef = ref<FormInstance>()
const formState = reactive<Partial<UserInfo>>({
  id: '',
  userCode: '',
  userName: '',
  mobilePhone: '',
  email: '',
  status: 1,
  password: '',
})

const rules = {
  userCode: [{ required: true, message: '请输入用户账号' }],
  userName: [{ required: true, message: '请输入用户名称' }],
  status: [{ required: true, message: '请选择状态' }],
}

const fetchData = async () => {
  try {
    loading.value = true
    const res = await pageUsers(queryParams)
    if (res.data?.data) {
      dataSource.value = res.data.data.items
      total.value = res.data.data.total
    }
  } catch (error) {
    message.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const onSearch = () => {
  queryParams.page = 1
  fetchData()
}

const onReset = () => {
  queryParams.keyword = ''
  queryParams.page = 1
  fetchData()
}

const onTableChange = (pagination: any) => {
  queryParams.page = pagination.current
  queryParams.pageSize = pagination.pageSize
  fetchData()
}

// CRUD Operations
const handleAdd = () => {
  modalTitle.value = '新增用户'
  Object.assign(formState, {
    id: '',
    userCode: '',
    userName: '',
    mobilePhone: '',
    email: '',
    status: 1,
    password: '',
  })
  modalVisible.value = true
}

const handleEdit = (record: UserInfo) => {
  modalTitle.value = '编辑用户'
  Object.assign(formState, { ...record, password: '' })
  modalVisible.value = true
}

const handleDelete = (id: string) => {
  Modal.confirm({
    title: '确认删除',
    icon: createVNode(ExclamationCircleOutlined),
    content: '确定要删除该用户吗？此操作不可撤销。',
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteUser(id)
        message.success('删除成功')
        fetchData()
      } catch (error) {
        message.error('删除失败')
      }
    },
  })
}

const handleModalOk = async () => {
  try {
    await formRef.value?.validateFields()
    confirmLoading.value = true
    
    if (formState.id) {
      const { password, ...rest } = formState
      await updateUser(formState.id, password ? formState : rest)
      message.success('更新成功')
    } else {
      await createUser(formState)
      message.success('创建成功')
    }
    
    modalVisible.value = false
    fetchData()
  } catch (error) {
    console.error('Validation/API error:', error)
  } finally {
    confirmLoading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="user-management">
    <a-card :bordered="false" class="search-card">
      <a-form layout="inline" :model="queryParams">
        <a-form-item label="关键字">
          <a-input v-model:value="queryParams.keyword" placeholder="账号/名称" allow-clear @press-enter="onSearch" />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="onSearch">
              <template #icon><SearchOutlined /></template>
              查询
            </a-button>
            <a-button @click="onReset">
              <template #icon><ReloadOutlined /></template>
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <a-card :bordered="false" class="table-card">
      <template #extra>
        <a-button type="primary" @click="handleAdd">
          <template #icon><PlusOutlined /></template>
          新增用户
        </a-button>
      </template>
      
      <a-table
        :columns="columns"
        :data-source="dataSource"
        :loading="loading"
        :pagination="{
          current: queryParams.page,
          pageSize: queryParams.pageSize,
          total: total,
          showSizeChanger: true,
          showTotal: (t) => `共 ${t} 条`
        }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 1 ? 'success' : 'error'">
              {{ record.status === 1 ? '启用' : '禁用' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleEdit(record)">编辑</a-button>
              <a-button type="link" size="small" danger @click="handleDelete(record.id)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Add/Edit Modal -->
    <a-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :confirm-loading="confirmLoading"
      @ok="handleModalOk"
      @cancel="modalVisible = false"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :rules="rules"
        layout="vertical"
      >
        <a-form-item label="用户账号" name="userCode">
          <a-input v-model:value="formState.userCode" placeholder="请输入用户账号" :disabled="!!formState.id" />
        </a-form-item>
        <a-form-item label="用户名称" name="userName">
          <a-input v-model:value="formState.userName" placeholder="请输入用户名称" />
        </a-form-item>
        <a-form-item label="密码" name="password" :required="!formState.id">
          <a-input-password v-model:value="formState.password" :placeholder="formState.id ? '留空表示不修改' : '请输入密码'" />
        </a-form-item>
        <a-form-item label="手机号" name="mobilePhone">
          <a-input v-model:value="formState.mobilePhone" placeholder="请输入手机号" />
        </a-form-item>
        <a-form-item label="邮箱" name="email">
          <a-input v-model:value="formState.email" placeholder="请输入邮箱" />
        </a-form-item>
        <a-form-item label="状态" name="status">
          <a-radio-group v-model:value="formState.status">
            <a-radio :value="1">启用</a-radio>
            <a-radio :value="0">禁用</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.user-management {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.search-card {
  border-radius: 8px;
}
.table-card {
  border-radius: 8px;
}
</style>
