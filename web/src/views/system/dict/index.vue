<script setup lang="ts">
import { ref, onMounted, reactive, createVNode } from 'vue'
import {
  pageDicts,
  createDict,
  updateDict,
  deleteDict,
  pageDictItems,
  createDictItem,
  updateDictItem,
  deleteDictItem,
  type DictInfo,
  type DictItemInfo,
} from '@/api/system-service'
import { message, Modal } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  ExclamationCircleOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons-vue'
import type { FormInstance } from 'ant-design-vue'

// --- Dictionary Management ---
const loading = ref(false)
const dataSource = ref<DictInfo[]>([])
const total = ref(0)
const queryParams = reactive({
  page: 1,
  pageSize: 10,
  keyword: '',
})

const columns = [
  { title: '字典名称', dataIndex: 'name', key: 'name' },
  { title: '字典编码', dataIndex: 'code', key: 'code' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime' },
  { title: '操作', key: 'action', fixed: 'right', width: 220 },
]

const modalVisible = ref(false)
const modalTitle = ref('新增字典')
const confirmLoading = ref(false)
const formRef = ref<FormInstance>()
const formState = reactive<Partial<DictInfo>>({
  id: '',
  name: '',
  code: '',
  description: '',
  status: 1,
})

const rules = {
  name: [{ required: true, message: '请输入字典名称' }],
  code: [{ required: true, message: '请输入字典编码' }],
}

const fetchData = async () => {
  try {
    loading.value = true
    const res = await pageDicts(queryParams)
    if (res.data?.data) {
      dataSource.value = res.data.data.items
      total.value = res.data.data.total
    }
  } catch (error) {
    message.error('获取字典列表失败')
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

const handleAdd = () => {
  modalTitle.value = '新增字典'
  Object.assign(formState, { id: '', name: '', code: '', description: '', status: 1 })
  modalVisible.value = true
}

const handleEdit = (record: DictInfo) => {
  modalTitle.value = '编辑字典'
  Object.assign(formState, { ...record })
  modalVisible.value = true
}

const handleDelete = (id: string) => {
  Modal.confirm({
    title: '确认删除',
    icon: createVNode(ExclamationCircleOutlined),
    content: '确定要删除该字典吗？此操作将同时删除下属所有字典项。',
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteDict(id)
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
      await updateDict(formState.id, formState)
      message.success('更新成功')
    } else {
      await createDict(formState)
      message.success('创建成功')
    }
    modalVisible.value = false
    fetchData()
  } finally {
    confirmLoading.value = false
  }
}

// --- Dictionary Item Management ---
const itemDrawerVisible = ref(false)
const currentDict = ref<DictInfo | null>(null)
const itemLoading = ref(false)
const itemDataSource = ref<DictItemInfo[]>([])
const itemTotal = ref(0)
const itemQueryParams = reactive({
  page: 1,
  pageSize: 10,
  dictCode: '',
})

const itemColumns = [
  { title: '显示标签', dataIndex: 'label', key: 'label' },
  { title: '数据值', dataIndex: 'value', key: 'value' },
  { title: '排序', dataIndex: 'sortNo', key: 'sortNo' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', key: 'action', width: 120 },
]

const itemModalVisible = ref(false)
const itemModalTitle = ref('新增字典项')
const itemFormRef = ref<FormInstance>()
const itemFormState = reactive<Partial<DictItemInfo>>({
  id: '',
  dictCode: '',
  label: '',
  value: '',
  sortNo: 1,
  status: 1,
})

const itemRules = {
  label: [{ required: true, message: '请输入显示标签' }],
  value: [{ required: true, message: '请输入数据值' }],
}

const handleManageItems = (record: DictInfo) => {
  currentDict.value = record
  itemQueryParams.dictCode = record.code
  itemQueryParams.page = 1
  itemDrawerVisible.value = true
  fetchItems()
}

const fetchItems = async () => {
  try {
    itemLoading.value = true
    const res = await pageDictItems(itemQueryParams)
    if (res.data?.data) {
      itemDataSource.value = res.data.data.items
      itemTotal.value = res.data.data.total
    }
  } finally {
    itemLoading.value = false
  }
}

const handleAddItem = () => {
  itemModalTitle.value = '新增字典项'
  Object.assign(itemFormState, {
    id: '',
    dictCode: currentDict.value?.code,
    label: '',
    value: '',
    sortNo: itemDataSource.value.length + 1,
    status: 1,
  })
  itemModalVisible.value = true
}

const handleEditItem = (record: DictItemInfo) => {
  itemModalTitle.value = '编辑字典项'
  Object.assign(itemFormState, { ...record })
  itemModalVisible.value = true
}

const handleDeleteItem = (id: string) => {
  Modal.confirm({
    title: '确认删除',
    icon: createVNode(ExclamationCircleOutlined),
    content: '确定要删除该字典项吗？',
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteDictItem(id)
        message.success('删除成功')
        fetchItems()
      } catch (error) {
        message.error('删除失败')
      }
    },
  })
}

const handleItemModalOk = async () => {
  try {
    await itemFormRef.value?.validateFields()
    if (itemFormState.id) {
      await updateDictItem(itemFormState.id, itemFormState)
      message.success('更新成功')
    } else {
      await createDictItem(itemFormState)
      message.success('创建成功')
    }
    itemModalVisible.value = false
    fetchItems()
  } finally {
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="dict-management">
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
          新增字典
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
        @change="(p: any) => { queryParams.page = p.current; queryParams.pageSize = p.pageSize; fetchData() }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 1 ? 'success' : 'error'">
              {{ record.status === 1 ? '启用' : '禁用' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleManageItems(record)">
                <template #icon><UnorderedListOutlined /></template>
                字典项
              </a-button>
              <a-button type="link" size="small" @click="handleEdit(record)">编辑</a-button>
              <a-button type="link" size="small" danger @click="handleDelete(record.id)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Dict Modal -->
    <a-modal v-model:visible="modalVisible" :title="modalTitle" :confirm-loading="confirmLoading" @ok="handleModalOk">
      <a-form ref="formRef" :model="formState" :rules="rules" layout="vertical">
        <a-form-item label="字典名称" name="name">
          <a-input v-model:value="formState.name" placeholder="请输入字典名称" />
        </a-form-item>
        <a-form-item label="字典编码" name="code">
          <a-input v-model:value="formState.code" placeholder="请输入字典编码" :disabled="!!formState.id" />
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="formState.description" placeholder="请输入描述" />
        </a-form-item>
        <a-form-item label="状态" name="status">
          <a-radio-group v-model:value="formState.status">
            <a-radio :value="1">启用</a-radio>
            <a-radio :value="0">禁用</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Item Drawer -->
    <a-drawer
      v-model:visible="itemDrawerVisible"
      :title="`字典项管理 - ${currentDict?.name}`"
      width="800px"
      @close="itemDrawerVisible = false"
    >
      <div class="drawer-content">
        <div class="table-operations" style="margin-bottom: 16px">
          <a-button type="primary" @click="handleAddItem">
            <template #icon><PlusOutlined /></template>
            新增项
          </a-button>
        </div>
        <a-table
          :columns="itemColumns"
          :data-source="itemDataSource"
          :loading="itemLoading"
          :pagination="{
            current: itemQueryParams.page,
            pageSize: itemQueryParams.pageSize,
            total: itemTotal,
            showSizeChanger: true,
            size: 'small'
          }"
          @change="(p: any) => { itemQueryParams.page = p.current; itemQueryParams.pageSize = p.pageSize; fetchItems() }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="record.status === 1 ? 'success' : 'error'">
                {{ record.status === 1 ? '启用' : '禁用' }}
              </a-tag>
            </template>
            <template v-if="column.key === 'action'">
              <a-space>
                <a-button type="link" size="small" @click="handleEditItem(record)">编辑</a-button>
                <a-button type="link" size="small" danger @click="handleDeleteItem(record.id)">删除</a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </div>
    </a-drawer>

    <!-- Item Modal -->
    <a-modal v-model:visible="itemModalVisible" :title="itemModalTitle" @ok="handleItemModalOk">
      <a-form ref="itemFormRef" :model="itemFormState" :rules="itemRules" layout="vertical">
        <a-form-item label="显示标签" name="label">
          <a-input v-model:value="itemFormState.label" placeholder="请输入显示标签" />
        </a-form-item>
        <a-form-item label="数据值" name="value">
          <a-input v-model:value="itemFormState.value" placeholder="请输入数据值" />
        </a-form-item>
        <a-form-item label="排序" name="sortNo">
          <a-input-number v-model:value="itemFormState.sortNo" :min="1" style="width: 100%" />
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="itemFormState.description" placeholder="请输入描述" />
        </a-form-item>
        <a-form-item label="状态" name="status">
          <a-radio-group v-model:value="itemFormState.status">
            <a-radio :value="1">启用</a-radio>
            <a-radio :value="0">禁用</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.dict-management {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
