using UnityEngine;

public class FreeCam : MonoBehaviour
{
    [SerializeField] float m_MovementSpeed = 10f;
    [SerializeField] float m_FastMovementSpeed = 100f;
    [SerializeField] float m_FreeLookSensitivity = 3f;
    [SerializeField] float m_ZoomSensitivity = 10f;
    [SerializeField] float m_FastZoomSensitivity = 50f;

    bool m_Looking;

    float m_Yaw;
    float m_Pitch;

    void Start()
    {
        Vector3 angles = transform.localEulerAngles;
        m_Yaw = angles.y;

        // 0~360 값을 -180~180 느낌으로 보정
        m_Pitch = angles.x;
        if (m_Pitch > 180f)
            m_Pitch -= 360f;
    }

    void Update()
    {
        var fastMode = Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
        var movementSpeed = fastMode ? m_FastMovementSpeed : m_MovementSpeed;

        if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow))
            transform.position += -transform.right * movementSpeed * Time.deltaTime;

        if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow))
            transform.position += transform.right * movementSpeed * Time.deltaTime;

        if (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow))
            transform.position += transform.forward * movementSpeed * Time.deltaTime;

        if (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow))
            transform.position += -transform.forward * movementSpeed * Time.deltaTime;

        if (Input.GetKey(KeyCode.Q))
            transform.position += -transform.up * movementSpeed * Time.deltaTime;

        if (Input.GetKey(KeyCode.E))
            transform.position += transform.up * movementSpeed * Time.deltaTime;

        if (Input.GetKey(KeyCode.R) || Input.GetKey(KeyCode.PageUp))
            transform.position += Vector3.up * movementSpeed * Time.deltaTime;

        if (Input.GetKey(KeyCode.F) || Input.GetKey(KeyCode.PageDown))
            transform.position += -Vector3.up * movementSpeed * Time.deltaTime;

        if (m_Looking)
        {
            m_Yaw += Input.GetAxis("Mouse X") * m_FreeLookSensitivity;
            m_Pitch -= Input.GetAxis("Mouse Y") * m_FreeLookSensitivity;

            // 위아래 회전 제한
            m_Pitch = Mathf.Clamp(m_Pitch, -89f, 89f);

            transform.localRotation = Quaternion.Euler(m_Pitch, m_Yaw, 0f);
        }

        var axis = Input.GetAxis("Mouse ScrollWheel");
        if (axis != 0)
        {
            var zoomSensitivity = fastMode ? m_FastZoomSensitivity : m_ZoomSensitivity;
            transform.position += transform.forward * axis * zoomSensitivity;
        }

        if (Input.GetKeyDown(KeyCode.Mouse1))
            StartLooking();
        else if (Input.GetKeyUp(KeyCode.Mouse1))
            StopLooking();
    }

    void OnDisable()
    {
        StopLooking();
    }

    void StartLooking()
    {
        m_Looking = true;
        Cursor.visible = false;
        Cursor.lockState = CursorLockMode.Locked;
    }

    void StopLooking()
    {
        m_Looking = false;
        Cursor.visible = true;
        Cursor.lockState = CursorLockMode.None;
    }
}