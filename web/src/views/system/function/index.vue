<script setup lang="ts">
import { ref, onMounted, reactive, createVNode } from 'vue'
import {
  pageFunctions,
  createFunction,
  updateFunction,
  deleteFunction,
  type FunctionInfo,
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
const dataSource = ref<FunctionInfo[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  pageSize: 10,
  keyword: '',
})

const columns = [
  { title: '功能名称', dataIndex: 'funcName', key: 'funcName' },
  { title: '功能编码', dataIndex: 'funcCode', key: 'funcCode' },
  { title: '功能类型', dataIndex: 'funcType', key: 'funcType' },
  { title: '状态', dataIndex: 'isDisable', key: 'isDisable' },
  { title: '操作', key: 'action', fixed: 'right', width: 150 },
]

// Modal State
const modalVisible = ref(false)
const modalTitle = ref('新增功能')
const confirmLoading = ref(false)
const formRef = ref<FormInstance>()
const formState = reactive<Partial<FunctionInfo>>({
  id: '',
  funcName: '',
  funcCode: '',
  funcType: 'DIR',
  isMenu: 1,
  isDisable: 0,
  appCode: '',
})

const rules = {
  funcName: [{ required: true, message: '请输入功能名称' }],
  funcCode: [{ required: true, message: '请输入功能编码' }],
}

const fetchData = async () => {
  try {
    loading.value = true
    const res = await pageFunctions(queryParams)
    if (res.data?.data) {
      dataSource.value = res.data.data.items
      total.value = res.data.data.total
    }
  } catch (error) {
    message.error('获取功能列表失败')
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
  modalTitle.value = '新增功能'
  Object.assign(formState, {
    id: '',
    funcName: '',
    funcCode: '',
    funcType: 'DIR',
    isMenu: 1,
    isDisable: 0,
    appCode: '',
  })
  modalVisible.value = true
}

const handleEdit = (record: FunctionInfo) => {
  modalTitle.value = '编辑功能'
  Object.assign(formState, { ...record })
  modalVisible.value = true
}

const handleDelete = (id: string) => {
  Modal.confirm({
    title: '确认删除',
    icon: createVNode(ExclamationCircleOutlined),
    content: '确定要删除该功能吗？此操作不可撤销。',
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteFunction(id)
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
      await updateFunction(formState.id, formState)
      message.success('更新成功')
    } else {
      await createFunction(formState)
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
  <div class="function-management">
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
          新增功能
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
          <template v-if="column.key === 'isDisable'">
            <a-tag :color="record.isDisable === 0 ? 'success' : 'error'">
              {{ record.isDisable === 0 ? '启用' : '禁用' }}
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
        <a-form-item label="功能名称" name="funcName">
          <a-input v-model:value="formState.funcName" placeholder="请输入功能名称" />
        </a-form-item>
        <a-form-item label="功能编码" name="funcCode">
          <a-input v-model:value="formState.funcCode" placeholder="请输入功能编码" />
        </a-form-item>
        <a-form-item label="功能类型" name="funcType">
          <a-select v-model:value="formState.funcType">
            <a-select-option value="DIR">目录</a-select-option>
            <a-select-option value="MENU">菜单</a-select-option>
            <a-select-option value="FUNC">功能</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="应用编码" name="appCode">
          <a-input v-model:value="formState.appCode" placeholder="请输入应用编码" />
        </a-form-item>
        <a-form-item label="是否菜单" name="isMenu">
          <a-radio-group v-model:value="formState.isMenu">
            <a-radio :value="1">是</a-radio>
            <a-radio :value="0">否</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="状态" name="isDisable">
          <a-radio-group v-model:value="formState.isDisable">
            <a-radio :value="0">启用</a-radio>
            <a-radio :value="1">禁用</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.function-management {
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
