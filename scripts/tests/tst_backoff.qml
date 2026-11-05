import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/services/Retry.js" as Retry

TestCase {
    name: "Backoff"

    function test_quick_exits_double_the_wait_up_to_a_minute() {
        let failures = 0;
        const waits = [];
        for (let i = 0; i < 7; i++) {
            failures = Retry.failures(failures, 500);
            waits.push(Retry.wait(2000, failures));
        }
        compare(Retry.wait(2000, 0), 2000);
        compare(waits, [4000, 8000, 16000, 32000, 60000, 60000, 60000]);
    }

    function test_a_long_run_starts_over() {
        compare(Retry.failures(4, 61000), 0);
        compare(Retry.wait(5000, 0), 5000);
    }
}
