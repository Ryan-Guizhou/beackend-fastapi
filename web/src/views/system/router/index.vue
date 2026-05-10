<script setup lang="ts">
import { ref, onMounted, reactive, createVNode } from 'vue'
import {
  pageRouters,
  createRouter,
  updateRouter,
  deleteRouter,
  type RouterInfo,
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
const dataSource = ref<RouterInfo[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  pageSize: 10,
  keyword: '',
})

const columns = [
  { title: '路由名称', dataIndex: 'routerName', key: 'routerName' },
  { title: '路由编码', dataIndex: 'routerCode', key: 'routerCode' },
  { title: '路由URL', dataIndex: 'routerUrl', key: 'routerUrl' },
  { title: '组件路径', dataIndex: 'filePath', key: 'filePath' },
  { title: '模块编码', dataIndex: 'moduleCode', key: 'moduleCode' },
  { title: '操作', key: 'action', fixed: 'right', width: 150 },
]

// Modal State
const modalVisible = ref(false)
const modalTitle = ref('新增路由')
const confirmLoading = ref(false)
const formRef = ref<FormInstance>()
const formState = reactive<Partial<RouterInfo>>({
  id: '',
  routerName: '',
  routerCode: '',
  routerUrl: '',
  filePath: '',
  moduleCode: '',
})

const rules = {
  routerName: [{ required: true, message: '请输入路由名称' }],
  routerCode: [{ required: true, message: '请输入路由编码' }],
  routerUrl: [{ required: true, message: '请输入路由URL' }],
  filePath: [{ required: true, message: '请输入组件路径' }],
}

const fetchData = async () => {
  try {
    loading.value = true
    const res = await pageRouters(queryParams)
    if (res.data?.data) {
      dataSource.value = res.data.data.items
      total.value = res.data.data.total
    }
  } catch (error) {
    message.error('获取路由列表失败')
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
  modalTitle.value = '新增路由'
  Object.assign(formState, {
    id: '',
    routerName: '',
    routerCode: '',
    routerUrl: '',
    filePath: '',
    moduleCode: '',
  })
  modalVisible.value = true
}

const handleEdit = (record: RouterInfo) => {
  modalTitle.value = '编辑路由'
  Object.assign(formState, { ...record })
  modalVisible.value = true
}

const handleDelete = (id: string) => {
  Modal.confirm({
    title: '确认删除',
    icon: createVNode(ExclamationCircleOutlined),
    content: '确定要删除该路由吗？此操作不可撤销。',
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteRouter(id)
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
      await updateRouter(formState.id, formState)
      message.success('更新成功')
    } else {
      await createRouter(formState)
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
  <div class="router-management">
    <a-card :bordered="false" class="search-card">
      <a-form layout="inline" :model="queryParams">
        <a-form-item label="关键字">
          <a-input v-model:value="queryParams.keyword" placeholder="名称/编码" allow-clear @press-enter="onSearch" />
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
          新增路由
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
        <a-form-item label="路由名称" name="routerName">
          <a-input v-model:value="formState.routerName" placeholder="请输入路由名称" />
        </a-form-item>
        <a-form-item label="路由编码" name="routerCode">
          <a-input v-model:value="formState.routerCode" placeholder="请输入路由编码" />
        </a-form-item>
        <a-form-item label="路由URL" name="routerUrl">
          <a-input v-model:value="formState.routerUrl" placeholder="请输入路由URL (如: /system/user)" />
        </a-form-item>
        <a-form-item label="组件路径" name="filePath">
          <a-input v-model:value="formState.filePath" placeholder="请输入组件路径 (如: system/user/UserManagement)" />
        </a-form-item>
        <a-form-item label="模块编码" name="moduleCode">
          <a-input v-model:value="formState.moduleCode" placeholder="请输入模块编码" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.router-management {
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
