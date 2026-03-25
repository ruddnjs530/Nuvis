using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Robot;

public enum ModuleType
{
    None = 0,
    AirPurifier = 1,
    Humidifier = 2,
    Dehumidifier = 3
}

[System.Serializable]
public class ModuleVisualData
{
    public ModuleType moduleType;
    public GameObject equippedObject;
    public GameObject movingBoxPrefab;
}

public class RobotModuleSubscriber : MonoBehaviour
{
    [Header("ROS Topics")]
    [SerializeField] private string moduleStateTopic = "/robot/module/state";
    [SerializeField] private string moduleSwapEventTopic = "/robot/module/swap_event";

    [Header("Module State")]
    [SerializeField] private ModuleType currentModule = ModuleType.None;

    [Header("Module Visual")]
    [SerializeField] private List<ModuleVisualData> moduleVisualList = new List<ModuleVisualData>();

    [Header("Transfer Points")]
    [SerializeField] private Transform stationSpawnPoint;
    [SerializeField] private Transform robotAttachPoint;

    [Header("Animation")]
    [SerializeField] private float removeDuration = 0.35f;
    [SerializeField] private float removeDropDistance = 0.3f;
    [SerializeField] private float moveDuration = 1.0f;
    [SerializeField] private float moveArcHeight = 0.3f;
    [SerializeField] private float startDelayAfterRemove = 0.1f;

    private ROSConnection ros;
    private Dictionary<ModuleType, ModuleVisualData> moduleVisualMap = new Dictionary<ModuleType, ModuleVisualData>();

    private bool isChanging = false;
    private Coroutine changeCoroutine;
    private string lastHandledSwapKey = "";

    private const byte STATE_COMPLETED = 4;

    private ModuleType latestStateModule = ModuleType.None;
    private bool hasInitializedFromState = false;

    private void Awake()
    {
        foreach (var data in moduleVisualList)
        {
            if (!moduleVisualMap.ContainsKey(data.moduleType))
                moduleVisualMap.Add(data.moduleType, data);
        }
    }

    private void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();

        ros.Subscribe<ModuleStateMsg>(moduleStateTopic, OnReceiveModuleState);
        ros.Subscribe<ModuleSwapEventMsg>(moduleSwapEventTopic, OnReceiveSwapEvent);

        ApplyEquippedVisual(currentModule);
        Debug.Log($"[Module] 초기 모듈 상태: {currentModule}");
    }

    private void OnReceiveModuleState(ModuleStateMsg msg)
    {
        latestStateModule = ParseModuleType(msg.module_type);
        Debug.Log($"[Module][State] module_type={msg.module_type}, parsed={latestStateModule}");
    }

    private void OnReceiveSwapEvent(ModuleSwapEventMsg msg)
    {
        Debug.Log($"[Module][SwapEvent] state={msg.state}, success={msg.success}, from={msg.from_module_type}, to={msg.to_module_type}, task_id={msg.task_id}, command_id={msg.command_id}");

        if (msg.state != STATE_COMPLETED || !msg.success)
            return;

        string eventKey = $"{msg.task_id}:{msg.command_id}:{msg.state}:{msg.to_module_type}";
        if (lastHandledSwapKey == eventKey)
            return;

        lastHandledSwapKey = eventKey;

        ModuleType newModule = ParseModuleType(msg.to_module_type);
        RequestModuleChange(newModule);
    }

    private ModuleType ParseModuleType(byte value)
    {
        switch (value)
        {
            case 1: return ModuleType.AirPurifier;
            case 2: return ModuleType.Humidifier;
            case 3: return ModuleType.Dehumidifier;
            default: return ModuleType.None;
        }
    }

    private void RequestModuleChange(ModuleType newModule)
    {
        if (isChanging)
        {
            Debug.Log("[Module] 현재 교체 중입니다.");
            return;
        }

        if (currentModule == newModule && latestStateModule == newModule)
        {
            Debug.Log($"[Module] 이미 {newModule} 모듈입니다.");
            return;
        }

        if (changeCoroutine != null)
            StopCoroutine(changeCoroutine);

        changeCoroutine = StartCoroutine(ChangeModuleRoutine(newModule));
    }

    private IEnumerator ChangeModuleRoutine(ModuleType newModule)
    {
        isChanging = true;

        if (stationSpawnPoint == null || robotAttachPoint == null)
        {
            currentModule = newModule;
            ApplyEquippedVisual(currentModule);
            isChanging = false;
            changeCoroutine = null;
            yield break;
        }

        if (!moduleVisualMap.TryGetValue(newModule, out ModuleVisualData targetData))
        {
            Debug.LogWarning($"[Module] {newModule}에 해당하는 visual data가 없습니다.");
            isChanging = false;
            changeCoroutine = null;
            yield break;
        }

        Debug.Log($"[Module] 모듈 교체 시작: {currentModule} -> {newModule}");

        // 기존 장착 모듈 제거 애니메이션
        if (currentModule != ModuleType.None && moduleVisualMap.TryGetValue(currentModule, out ModuleVisualData currentData))
        {
            if (currentData.equippedObject != null && currentData.equippedObject.activeSelf)
            {
                Debug.Log("[Module] 기존 모듈 제거 시작");
                yield return StartCoroutine(AnimateRemoveCurrentModule(currentData.equippedObject));
            }
        }

        if (startDelayAfterRemove > 0f)
            yield return new WaitForSeconds(startDelayAfterRemove);

        // 박스 생성
        GameObject movingBox = null;
        if (targetData.movingBoxPrefab != null)
        {
            movingBox = Instantiate(
                targetData.movingBoxPrefab,
                stationSpawnPoint.position,
                stationSpawnPoint.rotation);

            movingBox.SetActive(true);
        }

        // 박스 이동
        float elapsed = 0f;
        Vector3 startPos = stationSpawnPoint.position;
        Vector3 endPos = robotAttachPoint.position;
        Quaternion startRot = stationSpawnPoint.rotation;
        Quaternion endRot = robotAttachPoint.rotation;

        while (elapsed < moveDuration)
        {
            elapsed += Time.deltaTime;
            float t = Mathf.Clamp01(elapsed / moveDuration);

            if (movingBox != null)
            {
                Vector3 pos = Vector3.Lerp(startPos, endPos, t);
                pos.y += Mathf.Sin(t * Mathf.PI) * moveArcHeight;

                movingBox.transform.position = pos;
                movingBox.transform.rotation = Quaternion.Slerp(startRot, endRot, t);
            }

            yield return null;
        }

        if (movingBox != null)
            Destroy(movingBox);

        currentModule = newModule;
        latestStateModule = newModule;
        ApplyEquippedVisual(currentModule);

        Debug.Log($"[Module] 모듈 교체 완료: {currentModule}");

        isChanging = false;
        changeCoroutine = null;
    }

    private IEnumerator AnimateRemoveCurrentModule(GameObject equippedObject)
    {
        Transform tr = equippedObject.transform;
        Vector3 originalLocalPos = tr.localPosition;
        Vector3 targetLocalPos = originalLocalPos + Vector3.down * removeDropDistance;

        float elapsed = 0f;

        while (elapsed < removeDuration)
        {
            elapsed += Time.deltaTime;
            float t = Mathf.Clamp01(elapsed / removeDuration);
            tr.localPosition = Vector3.Lerp(originalLocalPos, targetLocalPos, t);
            yield return null;
        }

        equippedObject.SetActive(false);
        tr.localPosition = originalLocalPos;
    }

    private void ApplyEquippedVisual(ModuleType module)
    {
        HideAllEquippedModules();

        if (moduleVisualMap.TryGetValue(module, out ModuleVisualData targetData))
        {
            if (targetData.equippedObject != null)
            {
                Transform targetTransform = targetData.equippedObject.transform;

                if (robotAttachPoint != null)
                {
                    targetTransform.SetParent(robotAttachPoint, false);
                    targetTransform.localPosition = Vector3.zero;
                    targetTransform.localRotation = Quaternion.identity;
                }

                targetData.equippedObject.SetActive(true);
            }
        }
    }

    private void HideAllEquippedModules()
    {
        foreach (var data in moduleVisualList)
        {
            if (data.equippedObject != null)
                data.equippedObject.SetActive(false);
        }
    }
}